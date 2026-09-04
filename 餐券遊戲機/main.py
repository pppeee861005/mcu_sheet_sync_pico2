# main.py
# CAT MEAL TICKET GAME

from machine import Pin, I2C
import ssd1306
import time


# OLED
i2c = I2C(
    0,
    sda=Pin(4),
    scl=Pin(5),
    freq=400000
)

oled = ssd1306.SSD1306_I2C(128, 64, i2c)


# Button
# GP15 ---- Button ---- GND
button = Pin(15, Pin.IN, Pin.PULL_UP)


# 一開始有 3 張餐券
tickets = 3


def cat_face():
    if tickets == 3:
        return "=^.^="
    elif tickets == 2:
        return "=^o^="
    elif tickets == 1:
        return "=^_^="
    else:
        return "=T.T="


def show_ticket():
    oled.fill(0)

    oled.text("CAT MEAL", 32, 0)
    oled.text("LEFT:", 40, 16)
    oled.text(str(tickets), 60, 32)

    # 最下面放貓咪
    oled.text(cat_face(), 40, 48)

    oled.show()


def show_yummy():
    oled.fill(0)

    oled.text("YUMMY!", 40, 16)
    oled.text("MEOW!", 44, 32)
    oled.text(cat_face(), 40, 48)

    oled.show()


# 第一次顯示
show_ticket()


while True:

    if button.value() == 0:

        if tickets > 0:

            tickets -= 1

            # 吃飯動畫
            show_yummy()
            time.sleep(0.8)

            # 回到主畫面
            show_ticket()

        # 等待放開按鈕
        while button.value() == 0:
            time.sleep_ms(10)

    time.sleep_ms(20)