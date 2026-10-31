# -*- coding: utf-8 -*-
"""
SkySync (天鏡同步儀) - 天氣監測與 Google 試算表即時同步系統
主控硬體：ESP32-S3 DevKitC-1
顯示器：0.96" OLED (SSD1306, I2C: SDA=GPIO21, SCL=GPIO22, 128x64)
按鍵輸入：
  - 左鍵：GPIO 18 (內部上拉，切換狀態 / 開機選單切換)
  - 右鍵：GPIO 4  (內部上拉，確認送出 / 開機選單確認連線)
"""

import time
import network
import urequests
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C

# ================= 雲端 API 設定 =================
GAS_URL = "https://script.google.com/macros/s/AKfycbwIi14pKmIsPCxihmJ31xqaVSj30XMGxdn5rQYyk35okmtZL1jRcPkDYQjbZVhL0aT6/exec"
DEVICE_NAME = "SkySync_ESP32"

# ================= Wi-Fi 熱點設定 =================
WIFI_CONFIGS = [
    {"ssid": "Redmi 13C", "pass": "chdmchkcrdfd7e8"},  # 優先手機熱點
    {"ssid": "egg5630", "pass": "27985630"}           # 備援家用 Wi-Fi
]

# ================= 硬體腳位定義 =================
I2C_SDA_PIN = 21
I2C_SCL_PIN = 22
BUTTON_LEFT_PIN = 18   # 左鍵：切換狀態 (Next)
BUTTON_RIGHT_PIN = 4   # 右鍵：確認送出 (Confirm / Send)

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
        "desc": "Water level: HIGH",
        "alert": "** DANGER WARNING **",
        "message": "Flood_Alert_Danger"
    }
]

# ================= 硬體初始化 =================
print("Initializing I2C and OLED...")
i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=400000)
oled = SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c)

btn_left = Pin(BUTTON_LEFT_PIN, Pin.IN, Pin.PULL_UP)
btn_right = Pin(BUTTON_RIGHT_PIN, Pin.IN, Pin.PULL_UP)

current_index = 0
switch_count = 0
is_dirty = False
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
        if is_dirty:
            oled.text("L:Next  R:[OK!]", 0, 52, 1)
        else:
            oled.text("L:Next  R:Send", 0, 52, 1)
    
    oled.show()

def show_splash(line1, line2="", line3=""):
    """開機/連網狀態提示畫面"""
    oled.fill(0)
    oled.fill_rect(0, 0, 128, 12, 1)
    oled.text("[ SkySync IoT ]", 4, 2, 0)
    oled.text(line1, 0, 20, 1)
    oled.text(line2, 0, 35, 1)
    oled.text(line3, 0, 50, 1)
    oled.show()

def select_and_connect_wifi():
    """開機雙鍵互動選單：左鍵切換 Wi-Fi，右鍵確認連線（5 秒自動倒數預設）"""
    global current_ip
    
    wifi_list = [
        {"name": "1. Redmi 13C (Phone)", "cfg": WIFI_CONFIGS[0]},
        {"name": "2. egg5630   (Home)",  "cfg": WIFI_CONFIGS[1]}
    ]
    selected_idx = 0
    timeout_seconds = 5
    start_tick = time.time()
    last_sec_displayed = -1
    
    def render_menu(idx, sec_left):
        oled.fill(0)
        oled.fill_rect(0, 0, 128, 13, 1)
        oled.text(f"Select Wi-Fi ({sec_left}s)", 2, 3, 0)
        
        prefix1 = "> " if idx == 0 else "  "
        oled.text(prefix1 + "Redmi 13C (Phone)", 0, 20, 1)
        
        prefix2 = "> " if idx == 1 else "  "
        oled.text(prefix2 + "egg5630   (Home)", 0, 34, 1)
        
        oled.hline(0, 48, 128, 1)
        oled.text("L:Next  R:Connect", 0, 52, 1)
        oled.show()
        
    render_menu(selected_idx, timeout_seconds)
    print("=== 開機 Wi-Fi 選擇 (左鍵切換，右鍵確認，5秒自動連預設) ===")
    
    last_left = 1
    last_right = 1
    
    while True:
        elapsed = time.time() - start_tick
        sec_left = max(0, timeout_seconds - elapsed)
        
        if sec_left != last_sec_displayed:
            last_sec_displayed = sec_left
            render_menu(selected_idx, sec_left)
            
        if elapsed >= timeout_seconds:
            target_cfg = wifi_list[selected_idx]["cfg"]
            print(f">> [超時自動連線] 連線至: {target_cfg['ssid']}")
            break
            
        val_l = btn_left.value()
        val_r = btn_right.value()
        
        # 左鍵切換 (GPIO 18)
        if last_left == 1 and val_l == 0:
            time.sleep_ms(30)
            if btn_left.value() == 0:
                selected_idx = (selected_idx + 1) % len(wifi_list)
                start_tick = time.time()
                print(f">> 切換選擇: {wifi_list[selected_idx]['name']}")
                render_menu(selected_idx, timeout_seconds)
                while btn_left.value() == 0:
                    time.sleep_ms(20)
                    
        # 右鍵手動確認 (GPIO 4)
        if last_right == 1 and val_r == 0:
            time.sleep_ms(30)
            if btn_right.value() == 0:
                target_cfg = wifi_list[selected_idx]["cfg"]
                print(f">> [手動確認選擇] 連線至: {target_cfg['ssid']}")
                while btn_right.value() == 0:
                    time.sleep_ms(20)
                break
                
        last_left = val_l
        last_right = val_r
        time.sleep_ms(20)
        
    # 開始連線所選 Wi-Fi
    wlan = network.WLAN(network.STA_IF)
    if not wlan.active():
        wlan.active(True)
    time.sleep_ms(200)
    
    ssid = target_cfg["ssid"]
    pwd = target_cfg["pass"]
    
    print(f"Connecting to Wi-Fi: {ssid} ...")
    show_splash("Connecting Wi-Fi:", ssid[:15], "Please wait...")
    
    try:
        wlan.disconnect()
        time.sleep_ms(200)
    except:
        pass
        
    try:
        wlan.connect(ssid, pwd)
    except Exception as e:
        print(f"wlan.connect error: {e}")
    
    start_time = time.time()
    dot_count = 0
    while not wlan.isconnected():
        if time.time() - start_time > 15:
            print(f"Timeout connecting to {ssid}")
            break
        time.sleep_ms(500)
        dot_count = (dot_count % 3) + 1
        show_splash("Connecting Wi-Fi:", ssid[:15], "." * dot_count)
        
    if wlan.isconnected():
        current_ip = wlan.ifconfig()[0]
        print(f"Wi-Fi Connected! SSID: {ssid}, IP: {current_ip}")
        show_splash("Wi-Fi Connected!", f"SSID: {ssid}", f"IP: {current_ip}")
        time.sleep(1.5)
        return True
    else:
        print(f"Wi-Fi {ssid} 連線失敗，進入離線模式")
        show_splash("Wi-Fi Failed!", "Running Offline", "Check Password")
        time.sleep(1.5)
        return False

def sync_to_google_sheet(state, count):
    """將當前狀態透過 GET Query URL 上報至 Google Apps Script (附帶斷線自動重連)"""
    wlan = network.WLAN(network.STA_IF)
    
    # 若 Wi-Fi 斷線，嘗試快速重連
    if not wlan.isconnected():
        print("Wi-Fi 斷線，嘗試重新連線...")
        render_ui(state, count, "Reconnecting...")
        for cfg in WIFI_CONFIGS:
            try:
                wlan.connect(cfg["ssid"], cfg["pass"])
                t_re = time.time()
                while not wlan.isconnected() and time.time() - t_re < 6:
                    time.sleep_ms(300)
                if wlan.isconnected():
                    break
            except:
                pass
                
    if not wlan.isconnected():
        print("Wi-Fi not connected. Skipping upload.")
        render_ui(state, count, "Offline Mode")
        time.sleep(1.5)
        return False
        
    event_str = f"Weather_{state['id']}"
    msg = state["message"]
    query_url = f"{GAS_URL}?event={event_str}&count={count}&msg={msg}"
    
    print(f">> Syncing to Google Sheet via GET: event={event_str}, count={count}")
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
    global current_index, switch_count, is_dirty
    print("=" * 45)
    print("SkySync - Weather & Google Sheet Sync (Dual Button)")
    print("  - Left (GPIO 18): Next State")
    print("  - Right (GPIO 4): Confirm & Send")
    print("=" * 45)
    
    # 步驟 1: 開機 Wi-Fi 二選一選單
    select_and_connect_wifi()
    
    # 步驟 2: 初始畫面
    render_ui(WEATHER_STATES[current_index], switch_count)
    
    # 開機初始狀態自動同步
    sync_to_google_sheet(WEATHER_STATES[current_index], switch_count)
    is_dirty = False
    render_ui(WEATHER_STATES[current_index], switch_count)
    
    last_left_state = 1
    last_right_state = 1
    
    # 步驟 3: 主迴圈按鍵監聽
    while True:
        val_left = btn_left.value()
        val_right = btn_right.value()
        
        # 1. 左鍵按下 (GPIO 18): 切換選項 (Next)
        if last_left_state == 1 and val_left == 0:
            time.sleep_ms(30)
            if btn_left.value() == 0:
                current_index = (current_index + 1) % len(WEATHER_STATES)
                is_dirty = True
                state = WEATHER_STATES[current_index]
                print(f">> [左鍵: 切換] -> {state['id']} (待確認送出)")
                render_ui(state, switch_count)
                
                # 釋放按鍵並加入超時保護 (最多等 1 秒，防按鍵接觸卡死)
                t_rel = time.time()
                while btn_left.value() == 0 and (time.time() - t_rel < 1):
                    time.sleep_ms(20)
                    
        # 2. 右鍵按下 (GPIO 4): 確認送出 (Confirm / Send)
        if last_right_state == 1 and val_right == 0:
            time.sleep_ms(30)
            if btn_right.value() == 0:
                switch_count += 1
                state = WEATHER_STATES[current_index]
                print(f">> [右鍵: 確認 #{switch_count}] 送出狀態: {state['id']} 至試算表...")
                
                # 釋放按鍵並加入超時保護
                t_rel = time.time()
                while btn_right.value() == 0 and (time.time() - t_rel < 1):
                    time.sleep_ms(20)
                
                # 同步上報 Google 試算表
                sync_to_google_sheet(state, switch_count)
                is_dirty = False
                render_ui(state, switch_count)
                
        last_left_state = val_left
        last_right_state = val_right
        time.sleep_ms(20)

if __name__ == "__main__":
    main()
