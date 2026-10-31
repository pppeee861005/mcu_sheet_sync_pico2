# -*- coding: utf-8 -*-
"""
天氣/災害狀態監測儀與 Google 試算表即時同步 (MCU Sheet Sync)
主控硬體：ESP32-S3 DevKitC-1
顯示器：0.96" OLED (SSD1306, I2C: SDA=GPIO21, SCL=GPIO22, 128x64)
按鍵輸入：GPIO 18 (內部上拉，按下為 LOW)

互動邏輯：
  1. 開機自動連線 Wi-Fi（優先家用 egg5630，失敗切換手機熱點 Redmi 13C）。
  2. 進入天氣監控介面，按一下 GPIO 18 切換狀態：
     - 晴天 (SUNNY)
     - 大雨 (HEAVY RAIN)
     - 淹水 (FLOOD ALERT!)
  3. 切換後自動以 GET Query URL 發送至 Google Apps Script 雲端。
  4. 螢幕即時顯示「Syncing Sheet...」與「Sheet Synced! OK」。
"""

import time
import network
import urequests
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C

# ================= 雲端 API 設定 =================
GAS_URL = "https://script.google.com/macros/s/AKfycbwIi14pKmIsPCxihmJ31xqaVSj30XMGxdn5rQYyk35okmtZL1jRcPkDYQjbZVhL0aT6/exec"
DEVICE_NAME = "ESP32-S3_Weather"

# ================= Wi-Fi 熱點設定 =================
WIFI_CONFIGS = [
    {"ssid": "Redmi 13C", "pass": "chdmchkcrdfd7e8"},  # 優先手機熱點
    {"ssid": "egg5630", "pass": "27985630"}           # 備援家用 Wi-Fi
]

# ================= 硬體腳位定義 =================
I2C_SDA_PIN = 21
I2C_SCL_PIN = 22
BUTTON_PIN = 18

OLED_WIDTH = 128
OLED_HEIGHT = 64

# ================= 狀態定義 =================
WEATHER_STATES = [
    {
        "id": "SUNNY",
        "title": "[ SUNNY / Sunny ]",
        "icon_type": "sun",
        "desc": "Weather is clear",
        "alert": "Condition: Normal",
        "message": "Sunny_Clear"
    },
    {
        "id": "RAIN",
        "title": "[ HEAVY RAIN ]",
        "icon_type": "rain",
        "desc": "Rain: > 50 mm/hr",
        "alert": "Drive with care!",
        "message": "Heavy_Rain_Warning"
    },
    {
        "id": "FLOOD",
        "title": "[ FLOOD ALERT! ]",
        "icon_type": "flood",
        "desc": "Water Level: HIGH",
        "alert": "** DANGER WARNING **",
        "message": "Flood_Alert_Danger"
    }
]

# ================= 硬體初始化 =================
print("Initializing I2C and OLED...")
i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=400000)
oled = SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c)
btn = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

current_index = 0
switch_count = 0
current_ip = "Offline"

def draw_icon(icon_type):
    """繪製天氣圖標視覺效果 (x: 96~124, y: 16~44)"""
    cx, cy = 110, 30
    if icon_type == "sun":
        oled.fill_rect(cx - 5, cy - 5, 11, 11, 1)
        oled.line(cx, cy - 9, cx, cy - 6, 1)
        oled.line(cx, cy + 6, cx, cy + 9, 1)
        oled.line(cx - 9, cy, cx - 6, cy, 1)
        oled.line(cx + 6, cy, cx + 9, cy, 1)
        oled.line(cx - 7, cy - 7, cx - 5, cy - 5, 1)
        oled.line(cx + 5, cy + 5, cx + 7, cy + 7, 1)
        oled.line(cx - 7, cy + 7, cx - 5, cy + 5, 1)
        oled.line(cx + 5, cy - 5, cx + 7, cy - 7, 1)

    elif icon_type == "rain":
        oled.fill_rect(cx - 10, cy - 8, 20, 8, 1)
        oled.fill_rect(cx - 6, cy - 12, 12, 5, 1)
        oled.line(cx - 8, cy + 3, cx - 11, cy + 9, 1)
        oled.line(cx - 2, cy + 3, cx - 5, cy + 9, 1)
        oled.line(cx + 4, cy + 3, cx + 1, cy + 9, 1)
        oled.line(cx + 9, cy + 3, cx + 6, cy + 9, 1)

    elif icon_type == "flood":
        oled.line(cx, cy - 12, cx - 10, cy + 3, 1)
        oled.line(cx, cy - 12, cx + 10, cy + 3, 1)
        oled.line(cx - 10, cy + 3, cx + 10, cy + 3, 1)
        oled.line(cx, cy - 7, cx, cy - 2, 1)
        oled.pixel(cx, cy + 1, 1)
        oled.line(cx - 12, cy + 8, cx - 6, cy + 6, 1)
        oled.line(cx - 6, cy + 6, cx, cy + 8, 1)
        oled.line(cx, cy + 8, cx + 6, cy + 6, 1)
        oled.line(cx + 6, cy + 6, cx + 12, cy + 8, 1)

def render_ui(state, count, status_msg=None):
    """繪製完整 UI 介面到 OLED"""
    oled.fill(0)
    
    # 頂部狀態標題列（反白）
    oled.fill_rect(0, 0, 128, 13, 1)
    oled.text(state["title"], 2, 3, 0)
    
    # 左側資訊欄位
    oled.text(state["desc"], 0, 18, 1)
    oled.text(state["alert"], 0, 32, 1)
    
    # 右側圖標
    draw_icon(state["icon_type"])
    
    # 底部狀態列
    oled.hline(0, 48, 128, 1)
    if status_msg:
        oled.text(status_msg, 0, 52, 1)
    else:
        oled.text("Btn:Next [#{:02d}]".format(count), 0, 52, 1)
    
    oled.show()

def show_splash(line1, line2="", line3=""):
    """開機/連網狀態提示畫面"""
    oled.fill(0)
    oled.fill_rect(0, 0, 128, 12, 1)
    oled.text("[ Weather IoT ]", 4, 2, 0)
    oled.text(line1, 0, 20, 1)
    oled.text(line2, 0, 35, 1)
    oled.text(line3, 0, 50, 1)
    oled.show()

def connect_wifi():
    """自動輪詢連接 Wi-Fi"""
    global current_ip
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    for cfg in WIFI_CONFIGS:
        ssid = cfg["ssid"]
        pwd = cfg["pass"]
        print(f"Connecting to Wi-Fi: {ssid} ...")
        show_splash("Connecting Wi-Fi:", ssid[:15], "Please wait...")
        
        wlan.connect(ssid, pwd)
        start_time = time.time()
        while not wlan.isconnected():
            if time.time() - start_time > 12:
                print(f"Timeout connecting to {ssid}")
                break
            time.sleep_ms(300)
            
        if wlan.isconnected():
            current_ip = wlan.ifconfig()[0]
            print(f"Wi-Fi Connected! IP: {current_ip}")
            show_splash("Wi-Fi Connected!", f"SSID: {ssid}", f"IP: {current_ip}")
            time.sleep(1.5)
            return True
            
    print("All Wi-Fi connections failed. Operating in offline mode.")
    show_splash("Wi-Fi Failed!", "Running Offline", "Check AP/Hotspot")
    time.sleep(1.5)
    return False

def sync_to_google_sheet(state, count):
    """將當前狀態透過 GET Query URL 上報至 Google Apps Script"""
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        print("Wi-Fi not connected. Skipping upload.")
        render_ui(state, count, "Upload: No Wi-Fi")
        time.sleep(1.2)
        return False
        
    event_name = f"Weather_{state['id']}"
    msg = state["message"]
    query_url = f"{GAS_URL}?device={DEVICE_NAME}&event={event_name}&press_count={count}&message={msg}"
    
    print(f">> Syncing to Google Sheet via GET: event={event_name}, count={count}")
    render_ui(state, count, "Syncing Sheet...")
    
    try:
        response = urequests.get(query_url)
        status_code = response.status_code
        resp_text = response.text
        response.close()
        
        print(f">> Response [{status_code}]: {resp_text[:80]}")
        if status_code == 200:
            render_ui(state, count, "Sheet Synced! OK")
            time.sleep(1.5)
            return True
        else:
            render_ui(state, count, f"HTTP Err: {status_code}")
            time.sleep(1.5)
            return False
            
    except Exception as e:
        print(f"Upload failed with exception: {e}")
        render_ui(state, count, "Upload Error!")
        time.sleep(1.5)
        return False

def main():
    global current_index, switch_count
    print("=" * 45)
    print("ESP32-S3 Weather Monitor & Google Sheet Sync (Stable)")
    print("=" * 45)
    
    # 步驟 1: 連線 Wi-Fi
    connect_wifi()
    
    # 步驟 2: 初始畫面
    render_ui(WEATHER_STATES[current_index], switch_count)
    
    # 開機初始狀態自動同步
    sync_to_google_sheet(WEATHER_STATES[current_index], switch_count)
    render_ui(WEATHER_STATES[current_index], switch_count)
    
    last_btn_state = 1
    
    # 步驟 3: 主迴圈按鍵監聽
    while True:
        btn_val = btn.value()
        
        # 按下瞬間 (Pull-up: 1 -> 0)
        if last_btn_state == 1 and btn_val == 0:
            time.sleep_ms(30) # 防彈跳
            if btn.value() == 0:
                current_index = (current_index + 1) % len(WEATHER_STATES)
                switch_count += 1
                state = WEATHER_STATES[current_index]
                
                print(f">> [Button Pressed #{switch_count}] State: {state['id']}")
                render_ui(state, switch_count)
                
                # 等待按鈕放開
                while btn.value() == 0:
                    time.sleep_ms(20)
                
                # 同步上報 Google 試算表
                sync_to_google_sheet(state, switch_count)
                render_ui(state, switch_count)
                
        last_btn_state = btn_val
        time.sleep_ms(20)

if __name__ == "__main__":
    main()
