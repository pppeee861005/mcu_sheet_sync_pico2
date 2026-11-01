# main.py - LCD1602 雙按鈕計數器 (高穩定版)
import time
from machine import Pin, I2C
from pico_i2c_lcd import I2cLcd

# 1. 初始化按鈕 (GP14 與 GP16，開啟內部上拉電阻，按鈕另一端接 GND)
btn_add = Pin(14, Pin.IN, Pin.PULL_UP)
btn_sub = Pin(16, Pin.IN, Pin.PULL_UP)

# 2. 初始化 I2C (100kHz 最穩定)
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=100000)

devices = i2c.scan()
if not devices:
    print("【錯誤】找不到 I2C 裝置！")
    raise SystemExit

addr = devices[0]
print(f"【成功】LCD 位址: {hex(addr)}")

# 3. 初始化 LCD
lcd = I2cLcd(i2c, addr, 2, 16)
lcd.clear()

# 顯示固定標題
lcd.move_to(0, 0)
lcd.putstr("Button Counter")

count = 0

def refresh_screen():
    lcd.move_to(0, 1)
    # 用固定長度字串靠左覆蓋舊內容
    lcd.putstr(f"Count: {count:<9}")

refresh_screen()

last_state_add = 1
last_state_sub = 1

while True:
    curr_state_add = btn_add.value()
    curr_state_sub = btn_sub.value()

    # GP14 按下 (1 變 0) -> +1
    if last_state_add == 1 and curr_state_add == 0:
        count += 1
        refresh_screen()
        time.sleep_ms(150)  # 防彈跳延遲

    # GP16 按下 (1 變 0) -> -1
    if last_state_sub == 1 and curr_state_sub == 0:
        count -= 1
        refresh_screen()
        time.sleep_ms(150)  # 防彈跳延遲

    last_state_add = curr_state_add
    last_state_sub = curr_state_sub
    time.sleep_ms(20)
