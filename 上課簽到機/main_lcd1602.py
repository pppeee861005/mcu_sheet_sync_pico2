# main.py - 上課簽到機 (Pico 2 W + LCD1602 + 實體雙按鍵)
# 硬體規範相同：
#   GP0 (Pin 1)  -> I2C0 SDA
#   GP1 (Pin 2)  -> I2C0 SCL
#   GP14 (Pin 19) -> [切換按鍵] 選擇學生姓名 (Next Name)
#   GP16 (Pin 21) -> [確認按鍵] 確認簽到 (Confirm Check-in)

import time
import network
import urequests
from machine import Pin, I2C
from pico_i2c_lcd import I2cLcd
from config import WIFI_NETWORKS, GAS_CHECKIN_SCRIPT_ID, STUDENT_LIST

# -------------------------------------------------------------
# 硬體腳位定義
# -------------------------------------------------------------
I2C_SDA_PIN = 0    # GP0 (Pin 1)
I2C_SCL_PIN = 1    # GP1 (Pin 2)
BTN_SELECT  = 14   # GP14 (Pin 19) 切換選擇下一個學生
BTN_CONFIRM = 16   # GP16 (Pin 21) 確認並送出簽到

# -------------------------------------------------------------
# LCD1602 自訂點陣圖標 (5x8 點陣)
# -------------------------------------------------------------
# 0 號字元：✔ 勾選成功符號
ICON_CHECK = bytearray([
    0b00000,
    0b00001,
    0b00011,
    0b10110,
    0b11100,
    0b01000,
    0b00000,
    0b00000
])

# 1 號字元：➤ 選擇游標箭頭
ICON_ARROW = bytearray([
    0b00000,
    0b00100,
    0b00010,
    0b11111,
    0b00010,
    0b00100,
    0b00000,
    0b00000
])

# 2 號字元：👤 學生人物圖標
ICON_USER = bytearray([
    0b01110,
    0b01110,
    0b01110,
    0b00100,
    0b01110,
    0b10101,
    0b00100,
    0b01010
])

# -------------------------------------------------------------
# 模組初始化
# -------------------------------------------------------------
i2c = I2C(0, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=100000)
devices = i2c.scan()
if not devices:
    raise RuntimeError("未檢測到 I2C 設備，請檢查 LCD1602 接線 (GP0/GP1/VBUS)")

lcd_addr = devices[0]
lcd = I2cLcd(i2c, lcd_addr, 2, 16)
lcd.custom_char(0, ICON_CHECK)
lcd.custom_char(1, ICON_ARROW)
lcd.custom_char(2, ICON_USER)

btn_select  = Pin(BTN_SELECT,  Pin.IN, Pin.PULL_UP)
btn_confirm = Pin(BTN_CONFIRM, Pin.IN, Pin.PULL_UP)

# -------------------------------------------------------------
# 顯示工具函式
# -------------------------------------------------------------
def lcd_show_message(line1, line2=""):
    """安全清屏並顯示兩行訊息"""
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr(line1[:16])
    if line2:
        lcd.move_to(0, 1)
        lcd.putstr(line2[:16])

def typewriter_print(line, text, delay=0.04):
    """逐字微動態印出字串"""
    lcd.move_to(0, line)
    lcd.putstr(" " * 16)
    lcd.move_to(0, line)
    for ch in text[:16]:
        lcd.putchar(ch)
        time.sleep(delay)

def render_select_screen(current_name, index, total):
    """
    選人介面：
    Line 1: 👤 SELECT [1/10]
    Line 2: ➤ Alex Chen
    """
    lcd.clear()
    # 第一行：人物圖標 + 提示與編號
    lcd.move_to(0, 0)
    lcd.putchar(chr(2))
    header = f" SELECT [{index + 1}/{total}]"
    lcd.putstr(header[:15])

    # 第二行：箭頭圖標 + 學生姓名
    lcd.move_to(0, 1)
    lcd.putchar(chr(1))
    lcd.putstr(" ")
    lcd.putstr(current_name[:14])

# -------------------------------------------------------------
# 網路連線管理 (優先手機熱點，家用備援)
# -------------------------------------------------------------
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        return True

    for net in WIFI_NETWORKS:
        ssid = net.get("ssid", "")
        pwd = net.get("password", "")
        lcd_show_message("Connecting WiFi", ssid[:16])
        print(f"[WiFi] 嘗試連線至: {ssid}...")
        wlan.connect(ssid, pwd)

        start_time = time.time()
        while not wlan.isconnected():
            if time.time() - start_time > 10:
                print(f"[WiFi] 連線 {ssid} 逾時，嘗試下一組...")
                break
            time.sleep(0.5)

        if wlan.isconnected():
            ip = wlan.ifconfig()[0]
            print(f"[WiFi] 連線成功! IP: {ip}")
            lcd_show_message("WiFi Connected!", ip[:16])
            time.sleep(1.2)
            return True

    lcd_show_message("WiFi Failed!", "Check config.py")
    return False

# -------------------------------------------------------------
# 雲端簽到同步 (Google Apps Script API)
# -------------------------------------------------------------
def submit_checkin(student_name):
    """發送 HTTP GET 請求向雲端 Google 試算表記錄簽到"""
    # 簡易 URL 編碼空白
    encoded_name = student_name.replace(" ", "%20")
    url = f"https://script.google.com/macros/s/{GAS_CHECKIN_SCRIPT_ID}/exec?name={encoded_name}"
    print(f"[HTTP] 送出簽到請求: {student_name} -> {url}...")

    lcd.clear()
    typewriter_print(0, "Submitting...", delay=0.03)
    typewriter_print(1, f"-> {student_name[:12]}", delay=0.03)

    try:
        res = urequests.get(url)
        if res.status_code == 200:
            data = res.json()
            res.close()
            return data
        else:
            print(f"[HTTP] 伺服器異常碼: {res.status_code}")
            res.close()
            return None
    except Exception as e:
        print(f"[HTTP] 網路請求異常: {e}")
        return None

def show_checkin_result(data, student_name):
    """簽到成功 / 重複簽到反饋視覺畫面"""
    lcd.clear()
    if data and data.get("status") == "success":
        is_dup = data.get("is_duplicate", False)
        if is_dup:
            # 今日已簽過
            lcd.move_to(0, 0)
            lcd.putstr("Already Done!   ")
            lcd.move_to(0, 1)
            lcd.putstr(f"{student_name[:14]}")
            time.sleep(2)
        else:
            # 簽到成功
            lcd.move_to(0, 0)
            lcd.putchar(chr(0))  # ✔
            lcd.putstr(" ATTEND SUCCESS ")
            lcd.move_to(0, 1)
            lcd.putstr(f"OK: {student_name[:12]}")
            # 慶祝閃爍背光 2 次
            for _ in range(2):
                lcd.backlight_off()
                time.sleep(0.1)
                lcd.backlight_on()
                time.sleep(0.15)
            time.sleep(2.5)
    else:
        # 雲端異常但記錄本地成功 (離線或備援)
        lcd.move_to(0, 0)
        lcd.putchar(chr(0))
        lcd.putstr(" SIGNED (OFFLINE)")
        lcd.move_to(0, 1)
        lcd.putstr(f"OK: {student_name[:12]}")
        time.sleep(2)

# -------------------------------------------------------------
# 主程式 (狀態循環與雙按鍵邏輯)
# -------------------------------------------------------------
def main():
    lcd_show_message("Class Check-In", "System Booting..")
    time.sleep(1)

    # 確保連線 Wi-Fi
    connect_wifi()

    current_index = 0
    total_students = len(STUDENT_LIST)
    if total_students == 0:
        STUDENT_LIST.append("Student A")
        total_students = 1

    # 初次繪製選人畫面
    render_select_screen(STUDENT_LIST[current_index], current_index, total_students)

    while True:
        # [按鍵 1：GP14] 切換選擇學生名字
        if btn_select.value() == 0:
            time.sleep(0.05)  # 防彈跳
            if btn_select.value() == 0:
                current_index = (current_index + 1) % total_students
                student = STUDENT_LIST[current_index]
                print(f"[Select] 切換學生 [{current_index + 1}/{total_students}]: {student}")
                render_select_screen(student, current_index, total_students)
                # 等待按鈕放開
                while btn_select.value() == 0:
                    time.sleep(0.05)
                time.sleep(0.15)

        # [按鍵 2：GP16] 確認並送出簽到
        if btn_confirm.value() == 0:
            time.sleep(0.05)  # 防彈跳
            if btn_confirm.value() == 0:
                selected_name = STUDENT_LIST[current_index]
                print(f"[Confirm] 確認簽到: {selected_name}")
                
                # 送出簽到與反饋
                result_data = submit_checkin(selected_name)
                show_checkin_result(result_data, selected_name)

                # 簽到完成後，自動跳至下一位學生，方便下一位同學操作
                current_index = (current_index + 1) % total_students
                render_select_screen(STUDENT_LIST[current_index], current_index, total_students)

                # 等待確認鈕放開
                while btn_confirm.value() == 0:
                    time.sleep(0.05)
                time.sleep(0.2)

        time.sleep(0.05)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n系統離線。")
        lcd.clear()
        lcd.putstr("Check-in Offline")
