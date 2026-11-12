# main.py - 中文螢幕顯示 (ESP32-S3 + SSD1306 OLED 128x64 繁體中文展示)
# 硬體接線完全遵循：終極極客掌機/硬體架構.md
#   I2C SDA: GPIO 21
#   I2C SCL: GPIO 22
#   按鈕 A (左鍵/切換): GPIO 18 (Pull-Up)
#   按鈕 B (右鍵/確認): GPIO 4 (Pull-Up)
#   蜂鳴器: GPIO 33
#   板載 LED: GPIO 2

import time
from machine import Pin, I2C
import ssd1306
from fonts_cn import draw_char_16x16, draw_string_cn

# -------------------------------------------------------------
# 硬體腳位定義
# -------------------------------------------------------------
SDA_PIN = 21       # GPIO 21 (I2C0 SDA)
SCL_PIN = 22       # GPIO 22 (I2C0 SCL)
BTN_A_PIN = 18     # GPIO 18 (按鈕 A 左鍵)
BTN_B_PIN = 4      # GPIO 4  (按鈕 B 右鍵)
BUZZER_PIN = 33    # GPIO 33 (有源蜂鳴器)
LED_PIN = 2        # GPIO 2  (板載 LED)

WIDTH = 128
HEIGHT = 64

# -------------------------------------------------------------
# 模組初始化
# -------------------------------------------------------------
i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=400000)
oled = ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c)

btn_a = Pin(BTN_A_PIN, Pin.IN, Pin.PULL_UP)
btn_b = Pin(BTN_B_PIN, Pin.IN, Pin.PULL_UP)
buzzer = Pin(BUZZER_PIN, Pin.OUT)
led = Pin(LED_PIN, Pin.OUT)

buzzer.value(0)
led.value(0)

# -------------------------------------------------------------
# 提示音與燈光回饋
# -------------------------------------------------------------
def beep_ack():
    """按鍵短音回饋"""
    led.value(1)
    buzzer.value(1)
    time.sleep(0.04)
    buzzer.value(0)
    led.value(0)

def beep_confirm():
    """確認雙音回饋"""
    for _ in range(2):
        led.value(1)
        buzzer.value(1)
        time.sleep(0.06)
        buzzer.value(0)
        led.value(0)
        time.sleep(0.04)

# -------------------------------------------------------------
# 示範畫面輪播
# -------------------------------------------------------------
PAGES = [
    {
        "title": "中文螢幕顯示",
        "sub": "極客掌機",
        "desc": "ESP32-S3 OLED"
    },
    {
        "title": "上課簽到機",
        "sub": "簽到成功",
        "desc": "出席確認 OK"
    },
    {
        "title": "股市大盤機",
        "sub": "大盤",
        "desc": "TAIEX +148"
    }
]

def render_page(page_idx):
    """繪製指定的繁體中文展示頁面"""
    page = PAGES[page_idx]
    oled.fill(0)

    # 頂部裝飾外框
    oled.rect(0, 0, 128, 64, 1)
    oled.hline(0, 22, 128, 1)

    # 標題：16x16 繁體中文字
    draw_string_cn(oled, page["title"], 8, 3)

    # 副標題：16x16 繁體中文字
    draw_string_cn(oled, page["sub"], 12, 28)

    # 底部英數說明
    oled.text(page["desc"], 12, 48)

    oled.show()

# -------------------------------------------------------------
# 主程式
# -------------------------------------------------------------
def main():
    print("[OLED] 中文螢幕顯示系統啟動...")
    beep_ack()

    cur_page = 0
    total_pages = len(PAGES)
    render_page(cur_page)

    while True:
        # 按鈕 A (GPIO 18)：切換頁面
        if btn_a.value() == 0:
            time.sleep(0.05)
            if btn_a.value() == 0:
                beep_ack()
                cur_page = (cur_page + 1) % total_pages
                print(f"[Page] 切換頁面 -> {cur_page}")
                render_page(cur_page)
                while btn_a.value() == 0:
                    time.sleep(0.05)
                time.sleep(0.15)

        # 按鈕 B (GPIO 4)：確認/點亮蜂鳴器互動
        if btn_b.value() == 0:
            time.sleep(0.05)
            if btn_b.value() == 0:
                beep_confirm()
                print("[Action] 按鈕 B 確認觸發！")
                
                # 畫面短暫反白提示
                oled.invert(1)
                time.sleep(0.2)
                oled.invert(0)
                
                while btn_b.value() == 0:
                    time.sleep(0.05)
                time.sleep(0.15)

        time.sleep(0.05)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        oled.fill(0)
        oled.show()
        print("\n系統休眠。")
