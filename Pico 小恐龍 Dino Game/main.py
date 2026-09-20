from machine import Pin, I2C
from time import sleep_ms
import ssd1306
import random


# ESP32 常見接線
# OLED SDA -> GPIO 21，SCL -> GPIO 22
# 按鈕一端 -> GPIO 18，另一端 -> GND
SDA_PIN = 21
SCL_PIN = 22
BUTTON_PIN = 18

WIDTH = 128
HEIGHT = 64
GROUND_Y = 63

# 跳躍物理參數
JUMP_POWER = -8
GRAVITY = 1
FRAME_MS = 50
CACTUS_WIDTH = 6
CACTUS_HEIGHT = 10


i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=400000)
oled = ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c)
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)


dino_x = 12
dino_y = GROUND_Y - 12
velocity_y = 0
is_jumping = False
last_button = 1
cactus_x = WIDTH + 10
cactus_y = GROUND_Y - CACTUS_HEIGHT
game_over = False


def draw_dino(x, y):
    """繪製簡單的 12x12 像素恐龍。"""
    oled.fill_rect(x + 3, y, 6, 3, 1)
    oled.fill_rect(x + 1, y + 3, 10, 5, 1)
    oled.fill_rect(x, y + 8, 4, 4, 1)
    oled.fill_rect(x + 8, y + 8, 3, 4, 1)
    oled.pixel(x + 8, y + 1, 0)  # 眼睛


def draw_cactus(x, y):
    oled.fill_rect(x + 2, y, 3, CACTUS_HEIGHT, 1)
    oled.fill_rect(x, y + 3, 2, 3, 1)
    oled.fill_rect(x + 5, y + 5, 2, 3, 1)


def draw_game():
    oled.fill(0)
    oled.hline(0, GROUND_Y, WIDTH, 1)
    draw_dino(dino_x, int(dino_y))
    if cactus_x < WIDTH:
        draw_cactus(cactus_x, cactus_y)
    if game_over:
        oled.fill_rect(22, 20, 84, 24, 0)
        oled.rect(22, 20, 84, 24, 1)
        oled.text("GAME OVER", 32, 25)
        oled.text("PRESS JUMP", 28, 35)
    oled.show()


def start_jump():
    global velocity_y, is_jumping
    if not is_jumping:
        velocity_y = JUMP_POWER
        is_jumping = True


def update_physics():
    global dino_y, velocity_y, is_jumping

    if not is_jumping:
        return

    dino_y += velocity_y
    velocity_y += GRAVITY

    if dino_y >= GROUND_Y - 12:
        dino_y = GROUND_Y - 12
        velocity_y = 0
        is_jumping = False


def update_cactus():
    global cactus_x, game_over
    if game_over:
        return
    cactus_x -= 2
    if cactus_x < -CACTUS_WIDTH:
        cactus_x = WIDTH + random.randint(15, 45)

    dino_left = dino_x
    dino_right = dino_x + 12
    dino_top = int(dino_y)
    dino_bottom = dino_top + 12
    cactus_right = cactus_x + CACTUS_WIDTH
    if (dino_right > cactus_x and dino_left < cactus_right
            and dino_bottom > cactus_y and dino_top < GROUND_Y):
        game_over = True


oled.fill(0)
oled.text("ESP32 DINO", 22, 10)
oled.text("PRESS TO JUMP", 8, 28)
oled.show()
sleep_ms(1200)


while True:
    current_button = button.value()

    if last_button == 1 and current_button == 0:
        if game_over:
            game_over = False
            cactus_x = WIDTH + 25
            dino_y = GROUND_Y - 12
            velocity_y = 0
            is_jumping = False
        else:
            start_jump()

    last_button = current_button
    update_physics()
    update_cactus()
    draw_game()
    sleep_ms(FRAME_MS)
