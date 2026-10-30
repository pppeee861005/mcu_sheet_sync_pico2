# -*- coding: utf-8 -*-
"""
天氣/環境狀態切換介面 (Weather State Toggle UI)
硬體配置：
  - ESP32-S3 DevKitC-1
  - 0.96" OLED (SSD1306, I2C: SDA=GPIO21, SCL=GPIO22, 128x64)
  - 實體按鍵 (GPIO 18, 內部上拉，按下為 LOW)

功能：
  - 開機初始化 OLED 顯示。
  - 按下 GPIO 18 按鈕，輪流切換狀態：
      1. 晴天 (SUNNY)
      2. 大雨 (HEAVY RAIN)
      3. 淹水 (FLOOD ALERT!)
  - 介面包含視覺框線、狀態圖標效果與切換計數。
"""

import time
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C

# ================= 腳位定義 =================
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
        "alert": "Condition: Normal"
    },
    {
        "id": "RAIN",
        "title": "[ HEAVY RAIN ]",
        "icon_type": "rain",
        "desc": "Rain: > 50 mm/hr",
        "alert": "Drive with care!"
    },
    {
        "id": "FLOOD",
        "title": "[ FLOOD ALERT! ]",
        "icon_type": "flood",
        "desc": "Water Level: HIGH",
        "alert": "** DANGER WARNING **"
    }
]

# ================= 硬體初始化 =================
print("Initializing I2C and OLED...")
i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=400000)
oled = SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c)

# 按鍵輸入（內部上拉）
btn = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

current_index = 0
switch_count = 0

def draw_icon(icon_type):
    """在右側 (x: 96~124, y: 16~44) 繪製天氣圖標視覺效果"""
    cx, cy = 110, 30
    if icon_type == "sun":
        # 繪製太陽中心方塊與向外發射光芒
        oled.fill_rect(cx - 5, cy - 5, 11, 11, 1)
        # 上下左右光芒
        oled.line(cx, cy - 9, cx, cy - 6, 1)
        oled.line(cx, cy + 6, cx, cy + 9, 1)
        oled.line(cx - 9, cy, cx - 6, cy, 1)
        oled.line(cx + 6, cy, cx + 9, cy, 1)
        # 斜角光芒
        oled.line(cx - 7, cy - 7, cx - 5, cy - 5, 1)
        oled.line(cx + 5, cy + 5, cx + 7, cy + 7, 1)
        oled.line(cx - 7, cy + 7, cx - 5, cy + 5, 1)
        oled.line(cx + 5, cy - 5, cx + 7, cy - 7, 1)

    elif icon_type == "rain":
        # 繪製雲朵輪廓 + 雨滴斜線
        oled.fill_rect(cx - 10, cy - 8, 20, 8, 1)
        oled.fill_rect(cx - 6, cy - 12, 12, 5, 1)
        # 雨滴
        oled.line(cx - 8, cy + 3, cx - 11, cy + 9, 1)
        oled.line(cx - 2, cy + 3, cx - 5, cy + 9, 1)
        oled.line(cx + 4, cy + 3, cx + 1, cy + 9, 1)
        oled.line(cx + 9, cy + 3, cx + 6, cy + 9, 1)

    elif icon_type == "flood":
        # 繪製警告三角形外框與驚嘆號 + 水位波浪
        oled.line(cx, cy - 12, cx - 10, cy + 3, 1)
        oled.line(cx, cy - 12, cx + 10, cy + 3, 1)
        oled.line(cx - 10, cy + 3, cx + 10, cy + 3, 1)
        # 驚嘆號
        oled.line(cx, cy - 7, cx, cy - 2, 1)
        oled.pixel(cx, cy + 1, 1)
        # 底部水波線
        oled.line(cx - 12, cy + 8, cx - 6, cy + 6, 1)
        oled.line(cx - 6, cy + 6, cx, cy + 8, 1)
        oled.line(cx, cy + 8, cx + 6, cy + 6, 1)
        oled.line(cx + 6, cy + 6, cx + 12, cy + 8, 1)

def render_ui(state, count):
    """繪製完整 UI 介面到 OLED"""
    oled.fill(0)
    
    # 頂部狀態標題列
    oled.fill_rect(0, 0, 128, 13, 1)
    oled.text(state["title"], 4, 3, 0) # 反白字體
    
    # 左側資訊欄位
    oled.text(state["desc"], 0, 20, 1)
    oled.text(state["alert"], 0, 34, 1)
    
    # 右側圖標
    draw_icon(state["icon_type"])
    
    # 底部狀態列（分隔線與按鍵提示）
    oled.hline(0, 48, 128, 1)
    oled.text("Btn:Switch [#{:02d}]".format(count), 0, 52, 1)
    
    oled.show()

def main():
    global current_index, switch_count
    print("=" * 40)
    print("Weather State Monitor Started!")
    print("GPIO 18 Button: Press to toggle state")
    print("=" * 40)
    
    # 首次繪製初始狀態（晴天）
    render_ui(WEATHER_STATES[current_index], switch_count)
    
    last_btn_state = 1
    
    while True:
        btn_val = btn.value()
        
        # 偵測按下瞬間（由 1 變 0，內部 Pull-Up）
        if last_btn_state == 1 and btn_val == 0:
            time.sleep_ms(30) # 簡易硬體防彈跳
            if btn.value() == 0:
                current_index = (current_index + 1) % len(WEATHER_STATES)
                switch_count += 1
                state = WEATHER_STATES[current_index]
                
                print(">> [Switch #{}] State toggled to: {}".format(switch_count, state["id"]))
                render_ui(state, switch_count)
                
                # 等待按鈕放開
                while btn.value() == 0:
                    time.sleep_ms(20)
        
        last_btn_state = btn_val
        time.sleep_ms(20)

if __name__ == "__main__":
    main()
