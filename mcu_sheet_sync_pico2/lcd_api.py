# lcd_api.py - 修正版
import time

class LcdApi:
    LCD_CLR = 0x01
    LCD_HOME = 0x02
    LCD_ENTRY_MODE = 0x04
    LCD_ENTRY_INC = 0x02
    LCD_ON_CTRL = 0x08
    LCD_ON_DISPLAY = 0x04
    LCD_ON_CURSOR = 0x02
    LCD_ON_BLINK = 0x01
    LCD_FUNCTION = 0x20
    LCD_FUNCTION_2LINES = 0x08
    LCD_CGRAM = 0x40
    LCD_DDRAM = 0x80

    def __init__(self, num_lines, num_columns):
        self.num_lines = min(num_lines, 4)
        self.num_columns = min(num_columns, 40)
        self.cursor_x = 0
        self.cursor_y = 0
        self.init_display()

    def init_display(self):
        # 4-bit, 2 lines, 5x8 font
        cmd = self.LCD_FUNCTION
        if self.num_lines > 1:
            cmd |= self.LCD_FUNCTION_2LINES
        self.hal_write_command(cmd)
        time.sleep_ms(2)

        self.display_off()
        time.sleep_ms(2)
        self.clear()
        time.sleep_ms(2)
        self.hal_write_command(self.LCD_ENTRY_MODE | self.LCD_ENTRY_INC)
        time.sleep_ms(2)
        self.display_on()
        time.sleep_ms(2)

    def clear(self):
        self.hal_write_command(self.LCD_CLR)
        time.sleep_ms(3)
        self.hal_write_command(self.LCD_HOME)
        time.sleep_ms(3)
        self.cursor_x = 0
        self.cursor_y = 0

    def show_cursor(self):
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY | self.LCD_ON_CURSOR)

    def hide_cursor(self):
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY)

    def blink_cursor_on(self):
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY | self.LCD_ON_CURSOR | self.LCD_ON_BLINK)

    def blink_cursor_off(self):
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY)

    def display_on(self):
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY)

    def display_off(self):
        self.hal_write_command(self.LCD_ON_CTRL)

    def move_to(self, cursor_x, cursor_y):
        self.cursor_x = cursor_x
        self.cursor_y = cursor_y
        addr = cursor_x & 0x3f
        if cursor_y & 1:
            addr += 0x40
        if cursor_y & 2:
            addr += 0x14
        self.hal_write_command(self.LCD_DDRAM | addr)

    def putchar(self, char):
        if char == '\n':
            self.cursor_x = 0
            self.cursor_y = (self.cursor_y + 1) % self.num_lines
            self.move_to(self.cursor_x, self.cursor_y)
        else:
            self.hal_write_data(ord(char))
            self.cursor_x += 1
            if self.cursor_x >= self.num_columns:
                self.cursor_x = 0
                self.cursor_y = (self.cursor_y + 1) % self.num_lines
                self.move_to(self.cursor_x, self.cursor_y)

    def putstr(self, string):
        for char in string:
            self.putchar(char)

    def custom_char(self, location, charmap):
        location &= 0x7
        self.hal_write_command(self.LCD_CGRAM | (location << 3))
        time.sleep_us(50)
        for byte in charmap:
            self.hal_write_data(byte)
            time.sleep_us(50)
        self.move_to(self.cursor_x, self.cursor_y)
