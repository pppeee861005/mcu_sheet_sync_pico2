# main.py - 股票機 (Pico 2 W 大盤指數監控機)
# 支援多 Wi-Fi 連線容錯、GAS 輕量 API 串接、LCD1602 自訂漲跌圖標、GP14 實體按鍵隨按隨刷

import time
import network
import urequests
from machine import Pin, I2C
from pico_i2c_lcd import I2cLcd
from config import WIFI_NETWORKS, GAS_SCRIPT_ID

# -------------------------------------------------------------
# 硬體腳位定義 (遵循 mcu_sheet_sync_pico2 規範)
# -------------------------------------------------------------
I2C_SDA_PIN = 0   # GP0 (Pin 1)
I2C_SCL_PIN = 1   # GP1 (Pin 2)
BTN_REFRESH = 14  # GP14 (Pin 19) 手動立即刷新
BTN_TOGGLE  = 16  # GP16 (Pin 21) 切換背光

UPDATE_INTERVAL_SEC = 180  # 每 3 分鐘自動更新一次大盤

# -------------------------------------------------------------
# LCD1602 自訂點陣圖標 (5x8 點陣)
# -------------------------------------------------------------
# 0 號字元：▲ 漲
ICON_UP = bytearray([
    0b00100,
    0b01110,
    0b11111,
    0b00100,
    0b00100,
    0b00100,
    0b00000,
    0b00000
])

# 1 號字元：▼ 跌
ICON_DOWN = bytearray([
    0b00100,
    0b00100,
    0b00100,
    0b11111,
    0b01110,
    0b00100,
    0b00000,
    0b00000
])

# 2 號字元：Wi-Fi 圖標
ICON_WIFI = bytearray([
    0b00000,
    0b01110,
    0b10001,
    0b00100,
    0b01010,
    0b00000,
    0b00100,
    0b00000
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
lcd.custom_char(0, ICON_UP)
lcd.custom_char(1, ICON_DOWN)
lcd.custom_char(2, ICON_WIFI)

btn_refresh = Pin(BTN_REFRESH, Pin.IN, Pin.PULL_UP)
btn_toggle  = Pin(BTN_TOGGLE,  Pin.IN, Pin.PULL_UP)
backlight_on = True

def lcd_show_message(line1, line2=""):
    """安全清屏並顯示兩行訊息"""
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr(line1[:16])
    if line2:
        lcd.move_to(0, 1)
        lcd.putstr(line2[:16])

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
            time.sleep(1.5)
            return True

    lcd_show_message("WiFi Failed!", "Check config.py")
    return False

# -------------------------------------------------------------
# GAS API 行情抓取
# -------------------------------------------------------------
def fetch_stock_data():
    """向 Google Apps Script 獲取最新大盤資料"""
    url = f"https://script.google.com/macros/s/{GAS_SCRIPT_ID}/exec"
    print(f"[HTTP] 請求中繼 API: {url}...")
    try:
        # Google Apps Script 遵循 302 重導向
        res = urequests.get(url)
        if res.status_code == 200:
            data = res.json()
            res.close()
            return data
        else:
            print(f"[HTTP] 回應狀態碼異常: {res.status_code}")
            res.close()
            return None
    except Exception as e:
        print(f"[HTTP] 請求異常: {e}")
        return None

def update_display(data):
    """更新 LCD1602 顯示畫面"""
    if not data or data.get("status") != "success":
        lcd_show_message("Data Error", "Retry shortly...")
        return

    # 範例數據格式：
    # index: "23,522.53" -> 精簡為 "23522.5" 或直接塞入
    raw_idx = data.get("index", "").replace(",", "")
    change = data.get("change", "0.00")
    direction = data.get("direction", "FLAT")

    # 第一行：TAIEX: 23522.53
    line1 = f"TAIEX: {raw_idx}"
    
    # 第二行：CHG: +148.87 與箭頭圖標
    line2 = f"CHG: {change}"
    
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr(line1[:16])
    
    lcd.move_to(0, 1)
    lcd.putstr(line2[:14])
    
    # 放置對應箭頭
    lcd.move_to(15, 1)
    if direction == "UP":
        lcd.putchar(chr(0))  # ▲
    elif direction == "DOWN":
        lcd.putchar(chr(1))  # ▼
    else:
        lcd.putstr("=")

# -------------------------------------------------------------
# 主迴圈
# -------------------------------------------------------------
def main():
    global backlight_on
    lcd_show_message("TAIEX Stock Bot", "Booting up...")
    time.sleep(1)

    if not connect_wifi():
        time.sleep(3)

    last_update = 0
    cached_data = None

    while True:
        now = time.time()
        
        # 實體按鍵 1：GP14 隨按隨刷
        if btn_refresh.value() == 0:
            lcd_show_message("Refreshing...", "Fetching TWSE...")
            cached_data = fetch_stock_data()
            if cached_data:
                update_display(cached_data)
            last_update = now
            time.sleep(0.5)  # 防彈跳

        # 實體按鍵 2：GP16 開關 LCD 背光
        if btn_toggle.value() == 0:
            backlight_on = not backlight_on
            if backlight_on:
                lcd.backlight_on()
            else:
                lcd.backlight_off()
            time.sleep(0.3)  # 防彈跳

        # 定時輪詢更新
        if (now - last_update >= UPDATE_INTERVAL_SEC) or (cached_data is None):
            wlan = network.WLAN(network.STA_IF)
            if not wlan.isconnected():
                connect_wifi()
            
            lcd_show_message("Updating Quote", "Please wait...")
            data = fetch_stock_data()
            if data and data.get("status") == "success":
                cached_data = data
                update_display(cached_data)
                last_update = now
            else:
                print("[Main] 更新失敗，稍後重試")
                if cached_data:
                    update_display(cached_data)  # 維持顯示舊資料
                time.sleep(5)

        time.sleep(0.1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程式中止")
        lcd.clear()
        lcd.putstr("System Halted.")
