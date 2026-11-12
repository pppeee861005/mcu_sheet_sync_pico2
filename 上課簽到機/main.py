# main.py - 上課簽到機 v2.0 (ESP32-S3 + SSD1306 OLED 繁體中文掌機版)
# 硬體腳位規範 (完全對齊終極極客掌機/硬體架構.md)：
#   I2C SDA: GPIO 21
#   I2C SCL: GPIO 22
#   按鍵 A (左鍵 / 切換學生名字): GPIO 18 (Pull-Up)
#   按鍵 B (右鍵 / 確認簽到送出): GPIO 4 (Pull-Up)
#   有源蜂鳴器: GPIO 33
#   板載 LED: GPIO 2

import time
import network
import socket
import ssl
import json
import gc
from machine import Pin, I2C
import ssd1306
from fonts_cn import draw_char_16x16, draw_string_cn
from config import WIFI_NETWORKS, GAS_CHECKIN_SCRIPT_ID, STUDENT_LIST

# -------------------------------------------------------------
# 硬體腳位定義
# -------------------------------------------------------------
SDA_PIN = 21       # GPIO 21 (I2C0 SDA)
SCL_PIN = 22       # GPIO 22 (I2C0 SCL)
BTN_SELECT  = 18   # GPIO 18 (按鈕 A 左鍵: 切換學生名字)
BTN_CONFIRM = 4    # GPIO 4  (按鈕 B 右鍵: 確認簽到送出)
BUZZER_PIN  = 33   # GPIO 33 (有源蜂鳴器)
LED_PIN     = 2    # GPIO 2  (板載 LED)

WIDTH = 128
HEIGHT = 64

# -------------------------------------------------------------
# 模組初始化
# -------------------------------------------------------------
i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=400000)
oled = ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c)

btn_select  = Pin(BTN_SELECT,  Pin.IN, Pin.PULL_UP)
btn_confirm = Pin(BTN_CONFIRM, Pin.IN, Pin.PULL_UP)
buzzer      = Pin(BUZZER_PIN,  Pin.OUT)
led         = Pin(LED_PIN,     Pin.OUT)

buzzer.value(0)
led.value(0)

# -------------------------------------------------------------
# 音效與燈光反饋
# -------------------------------------------------------------
def beep_click():
    """按鍵切換短音"""
    led.value(1)
    buzzer.value(1)
    time.sleep(0.03)
    buzzer.value(0)
    led.value(0)

def beep_success():
    """簽到成功歡慶雙響"""
    for _ in range(2):
        led.value(1)
        buzzer.value(1)
        time.sleep(0.06)
        buzzer.value(0)
        led.value(0)
        time.sleep(0.05)

# -------------------------------------------------------------
# 畫面繪製函式
# -------------------------------------------------------------
def show_status_screen(line1_cn, line2_en=""):
    """全螢幕置中狀態提示"""
    oled.fill(0)
    oled.rect(0, 0, 128, 64, 1)
    draw_string_cn(oled, line1_cn, 16, 16)
    if line2_en:
        oled.text(line2_en[:16], 16, 40)
    oled.show()

def render_select_screen(name, index, total):
    """
    選人介面 (繁體中文 OLED 版)：
    居中呈現 16x16 姓名
    """
    oled.fill(0)
    oled.rect(0, 0, 128, 64, 1)
    oled.hline(0, 20, 128, 1)

    # 頂部標題與計數
    draw_string_cn(oled, "上課簽到機", 6, 2)
    counter_str = f"[{index + 1}/{total}]"
    oled.text(counter_str, 88, 6)

    # 中間學生姓名 (16x16 漢字)
    # 若為 5 字 (如: "講師 賴建安") 從 x=16 開始；3 字 (如: "陳大明") 從 x=28 開始
    if len(name) >= 5:
        oled.text(">", 4, 28)
        draw_string_cn(oled, name, 16, 24)
    else:
        oled.text(">", 12, 28)
        draw_string_cn(oled, name, 28, 24)

    # 底部按鍵指引
    oled.hline(0, 48, 128, 1)
    oled.text("L:Next  R:Sign", 8, 52)

    oled.show()

# -------------------------------------------------------------
# 網路連線管理 (優先手機熱點，家用備援，含 ESP32 異常防禦)
# -------------------------------------------------------------
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    try:
        wlan.active(False)
        time.sleep(0.2)
    except Exception:
        pass
    wlan.active(True)
    time.sleep(0.5)

    if wlan.isconnected():
        return True

    for net in WIFI_NETWORKS:
        ssid = net.get("ssid", "")
        pwd = net.get("password", "")
        show_status_screen("連線中", ssid[:14])
        print(f"[WiFi] 嘗試連線至: {ssid}...")
        
        try:
            # 若處於連線中狀態先斷開，避免 ESP32 拋出 Wifi Internal State Error
            try:
                wlan.disconnect()
            except Exception:
                pass
            time.sleep(0.2)
            wlan.connect(ssid, pwd)
        except Exception as e:
            print(f"[WiFi] 發起連線 {ssid} 異常: {e}，嘗試下一組...")
            continue

        start_time = time.time()
        while not wlan.isconnected():
            if time.time() - start_time > 8:
                print(f"[WiFi] 連線 {ssid} 逾時，嘗試下一組...")
                break
            time.sleep(0.5)

        if wlan.isconnected():
            ip = wlan.ifconfig()[0]
            print(f"[WiFi] 連線成功! IP: {ip}")
            show_status_screen("連線成功", ip[:16])
            time.sleep(1.0)
            return True

    show_status_screen("離線模式", "Offline Ready")
    time.sleep(1.0)
    return False

# -------------------------------------------------------------
# 雲端簽到同步 (強健型 SSL Socket 客戶端，徹底杜絕連線 EBUSY / 洩漏)
# -------------------------------------------------------------
def fetch_gas_request(url):
    """底層安全連線函式，具備 302 重導向追蹤與即時 Socket 關閉"""
    gc.collect()
    time.sleep(0.15)
    proto, dummy, host, path = url.split('/', 3)
    port = 443
    ai = socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM)
    addr = ai[0][-1]

    s = socket.socket()
    s.settimeout(15.0)
    try:
        s.connect(addr)
        s = ssl.wrap_socket(s, server_hostname=host)
        req = 'GET /' + path + ' HTTP/1.0\r\nHost: ' + host + '\r\nUser-Agent: ESP32-Attendance\r\nConnection: close\r\n\r\n'
        s.write(req.encode())

        response = b''
        while True:
            chunk = s.read(512)
            if not chunk:
                break
            response += chunk
        s.close()
        gc.collect()

        lines = response.split(b'\r\n')
        status_line = lines[0].decode()
        if '302' in status_line:
            for line in lines:
                if line.lower().startswith(b'location:'):
                    loc = line.split(b':', 1)[1].strip().decode()
                    return fetch_gas_request(loc)

        body = response.split(b'\r\n\r\n', 1)[1]
        return json.loads(body.decode())
    except Exception as e:
        try:
            s.close()
        except Exception:
            pass
        gc.collect()
        raise e

def submit_checkin(student_name):
    """發送 HTTP GET 請求向雲端 Google 試算表記錄簽到"""
    # URL 編碼 UTF-8
    encoded_name = ""
    for b in student_name.encode('utf-8'):
        encoded_name += "%%%02X" % b

    url = f"https://script.google.com/macros/s/{GAS_CHECKIN_SCRIPT_ID}/exec?name={encoded_name}"
    print(f"[HTTP] 送出簽到請求: {student_name} -> {url}...")

    oled.fill(0)
    oled.rect(0, 0, 128, 64, 1)
    draw_string_cn(oled, "簽到中", 40, 14)
    if len(student_name) >= 5:
        draw_string_cn(oled, student_name, 16, 34)
    else:
        draw_string_cn(oled, student_name, 40, 34)
    oled.show()

    try:
        data = fetch_gas_request(url)
        return data
    except Exception as e:
        print(f"[HTTP] 網路請求異常: {e}")
        return None

def show_checkin_result(data, student_name):
    """簽到成功 / 重複簽到反饋視覺畫面"""
    oled.fill(0)
    oled.rect(0, 0, 128, 64, 1)

    if data and data.get("status") == "success":
        is_dup = data.get("is_duplicate", False)
        if is_dup:
            # 今日已簽到
            draw_string_cn(oled, "已經簽到", 32, 14)
            draw_string_cn(oled, student_name, 40, 36)
            oled.show()
            beep_click()
            time.sleep(2)
        else:
            # 簽到成功
            draw_string_cn(oled, "簽到成功", 32, 14)
            draw_string_cn(oled, student_name, 40, 36)
            oled.show()
            
            # 螢幕反白歡慶閃爍
            oled.invert(1)
            beep_success()
            time.sleep(0.3)
            oled.invert(0)
            time.sleep(2)
    else:
        # 雲端異常但記錄本地成功
        draw_string_cn(oled, "出席確認", 32, 14)
        draw_string_cn(oled, student_name, 40, 36)
        oled.show()
        beep_success()
        time.sleep(2)

# -------------------------------------------------------------
# 主程式
# -------------------------------------------------------------
def main():
    print("[System] 上課簽到機 v2.0 (中文掌機版) 啟動...")
    beep_click()
    show_status_screen("學生簽到機", "Booting...")
    time.sleep(1)

    # Wi-Fi 自動連線
    connect_wifi()

    current_index = 0
    total_students = len(STUDENT_LIST)
    if total_students == 0:
        STUDENT_LIST.append("學生A")
        total_students = 1

    render_select_screen(STUDENT_LIST[current_index], current_index, total_students)

    while True:
        # [按鈕 A：GPIO 18 左鍵] 切換學生名字
        if btn_select.value() == 0:
            time.sleep(0.04)  # 防彈跳
            if btn_select.value() == 0:
                beep_click()
                current_index = (current_index + 1) % total_students
                student = STUDENT_LIST[current_index]
                print(f"[Select] 切換學生 [{current_index + 1}/{total_students}]: {student}")
                render_select_screen(student, current_index, total_students)
                while btn_select.value() == 0:
                    time.sleep(0.04)
                time.sleep(0.12)

        # [按鈕 B：GPIO 4 右鍵] 確認簽到
        if btn_confirm.value() == 0:
            time.sleep(0.04)
            if btn_confirm.value() == 0:
                selected_name = STUDENT_LIST[current_index]
                print(f"[Confirm] 確認簽到: {selected_name}")

                # 送出雲端打卡
                result_data = submit_checkin(selected_name)
                show_checkin_result(result_data, selected_name)

                # 簽到完成自動跳下一位同學
                current_index = (current_index + 1) % total_students
                render_select_screen(STUDENT_LIST[current_index], current_index, total_students)

                while btn_confirm.value() == 0:
                    time.sleep(0.04)
                time.sleep(0.15)

        time.sleep(0.04)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        oled.fill(0)
        oled.show()
        print("\n簽到系統休眠。")
