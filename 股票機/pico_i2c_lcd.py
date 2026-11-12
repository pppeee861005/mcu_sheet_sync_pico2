# pico_i2c_lcd.py
# 穩定版 MicroPython PCF8574 LCD1602 驅動 (加入脈衝延遲與穩定的 4-bit 握手初始化)

import time
from machine import I2C
from lcd_api import LcdApi

# PCF8574 腳位對應:
# P0: RS, P1: RW, P2: E, P3: Backlight, P4: D4, P5: D5, P6: D6, P7: D7
MASK_RS = 0x01
MASK_RW = 0x02
MASK_E  = 0x04
SHIFT_BACKLIGHT = 3
SHIFT_DATA = 4

class I2cLcd(LcdApi):
    def __init__(self, i2c, i2c_addr, num_lines, num_columns):
        self.i2c = i2c
        self.i2c_addr = i2c_addr
        self.implied_newline = False
        self.backlight = True
        
        # 開機等待 HD44780 電源穩定 (>40ms)
        time.sleep_ms(50)
        self.i2c.writeto(self.i2c_addr, bytes([0]))
        time.sleep_ms(20)
        
        # 嚴格依照 HD44780 4-bit 初始化時序：
        # 1. 0x03 三次
        self.hal_write_init_nibble(0x03)
        time.sleep_ms(5)
        self.hal_write_init_nibble(0x03)
        time.sleep_ms(5)
        self.hal_write_init_nibble(0x03)
        time.sleep_ms(1)
        # 2. 切換至 4-bit 模式 (0x02)
        self.hal_write_init_nibble(0x02)
        time.sleep_ms(1)
        
        # 初始化後續設定 (2行, 5x8點陣, 關閉顯示, 清除, 開啟顯示)
        super().__init__(num_lines, num_columns)

    def _pulse_enable(self, data):
        # 產生 E 脈衝 (High -> Low)，鎖存資料
        self.i2c.writeto(self.i2c_addr, bytes([data | MASK_E]))
        time.sleep_us(500)
        self.i2c.writeto(self.i2c_addr, bytes([data & ~MASK_E]))
        time.sleep_us(500)

    def hal_write_init_nibble(self, nibble):
        bl = 1 << SHIFT_BACKLIGHT if self.backlight else 0
        byte = bl | ((nibble & 0x0f) << SHIFT_DATA)
        self._pulse_enable(byte)

    def hal_backlight_on(self):
        self.backlight = True
        self.i2c.writeto(self.i2c_addr, bytes([1 << SHIFT_BACKLIGHT]))

    def hal_backlight_off(self):
        self.backlight = False
        self.i2c.writeto(self.i2c_addr, bytes([0]))

    def backlight_on(self):
        self.hal_backlight_on()

    def backlight_off(self):
        self.hal_backlight_off()

    def hal_write_command(self, cmd):
        bl = 1 << SHIFT_BACKLIGHT if self.backlight else 0
        high = bl | (((cmd >> 4) & 0x0f) << SHIFT_DATA)
        low  = bl | ((cmd & 0x0f) << SHIFT_DATA)
        self._pulse_enable(high)
        self._pulse_enable(low)
        if cmd <= 3:
            time.sleep_ms(5)

    def hal_write_data(self, data):
        bl = 1 << SHIFT_BACKLIGHT if self.backlight else 0
        high = MASK_RS | bl | (((data >> 4) & 0x0f) << SHIFT_DATA)
        low  = MASK_RS | bl | ((data & 0x0f) << SHIFT_DATA)
        self._pulse_enable(high)
        self._pulse_enable(low)
