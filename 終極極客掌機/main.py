# main.py - SkyDeck OS 終極極客版 (純離線全功能掌機)
# 主選單:
# 1. 小恐龍 (Chrome Dino Game)
# 2. 貓咪餐券 (Cat Meal Voucher 撕票/進食動畫)
# 3. 番茄鐘 (Pomodoro Focus Tracker 25m/5m/10m)
# 4. 極客時鐘與碼表 (Clock & Stopwatch)
# 硬體: ESP32-S3 (OLED SDA=21, SCL=22, 左鍵=GPIO 18, 右鍵=GPIO 4)

import time
import random
import gc
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C

# ================= 1. 硬體初始化 =================
I2C_SDA_PIN = 21
I2C_SCL_PIN = 22
BUTTON_LEFT_PIN = 18    # 左鍵 (Next / Jump / Mode)
BUTTON_RIGHT_PIN = 4    # 右鍵 (Enter / Confirm / Start)
BUZZER_PIN = 33         # 有源蜂鳴器 (正極接 GPIO 33, 負極接 GND)
LED_PIN = 2             # 板載內建 LED (GPIO 2)

WIDTH = 128
HEIGHT = 64

i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=400000)
oled = SSD1306_I2C(WIDTH, HEIGHT, i2c)

btn_left = Pin(BUTTON_LEFT_PIN, Pin.IN, Pin.PULL_UP)
btn_right = Pin(BUTTON_RIGHT_PIN, Pin.IN, Pin.PULL_UP)
buzzer = Pin(BUZZER_PIN, Pin.OUT)
buzzer.value(0)  # 預設靜音

led = Pin(LED_PIN, Pin.OUT)
led.value(0)     # 預設熄滅

def beep_click(duration_ms=18):
    """輕快的按鍵音效反饋"""
    buzzer.value(1)
    time.sleep_ms(duration_ms)
    buzzer.value(0)

def alarm_beep(times=3):
    """有源蜂鳴器與內建 LED 同步鬧鐘提醒 (急促逼逼聲 + 爆閃)"""
    for _ in range(times):
        buzzer.value(1)
        led.value(1)
        time.sleep_ms(150)
        buzzer.value(0)
        led.value(0)
        time.sleep_ms(100)

# ================= 2. 極客開機儀式感 =================
def play_boot_ceremony():
    oled.fill(0)
    for r in range(4):
        oled.fill(0)
        oled.hline(64 - r * 12, 32, r * 24, 1)
        oled.vline(64, 32 - r * 7, r * 14, 1)
        oled.show()
        time.sleep_ms(50)
        
    for step in range(0, 101, 25):
        oled.fill(0)
        oled.rect(14, 38, 100, 8, 1)
        oled.fill_rect(16, 40, int(step * 0.96), 4, 1)
        oled.text(">> SKYDECK OS <<", 4, 14, 1)
        oled.text(f"BOOTING {step}%", 24, 50, 1)
        oled.show()
        time.sleep_ms(60)

    oled.fill(0)
    oled.fill_rect(0, 4, 128, 14, 1)
    oled.text("* SKYDECK OS *", 10, 7, 0)
    oled.text("=================", 0, 24, 1)
    oled.text("  WELCOME, MAKER!", 0, 36, 1)
    oled.text("=================", 0, 48, 1)
    oled.show()
    time.sleep(1.2)

# ================= 3. 主選單 (4 大應用) =================
MENU_ITEMS = [
    {"title": "1. DINO GAME",  "desc": "Jump & Dodge"},
    {"title": "2. CAT VOUCHER","desc": "Tear & Feast"},
    {"title": "3. POMODORO",   "desc": "Focus Timer"},
    {"title": "4. GEEK CLOCK", "desc": "Stopwatch & Time"}
]

def show_main_menu():
    selected = 0
    last_l = 1
    last_r = 1

    def render():
        oled.fill(0)
        oled.fill_rect(0, 0, 128, 13, 1)
        oled.text("[ SKYDECK MENU ]", 2, 3, 0)
        
        # 顯示當前選中的項目
        oled.text(f"> {MENU_ITEMS[selected]['title']}", 0, 20, 1)
        oled.text(f"  {MENU_ITEMS[selected]['desc']}", 0, 34, 1)
        
        oled.hline(0, 48, 128, 1)
        oled.text("L:Next    R:Enter", 0, 52, 1)
        oled.show()

    render()

    while True:
        vl = btn_left.value()
        vr = btn_right.value()

        if last_l == 1 and vl == 0:
            beep_click(20)
            selected = (selected + 1) % len(MENU_ITEMS)
            render()
            time.sleep_ms(200)

        if last_r == 1 and vr == 0:
            beep_click(35)
            time.sleep_ms(200)
            return selected

        last_l = vl
        last_r = vr
        time.sleep_ms(20)

# ================= 應用 1: 小恐龍 (Dino Game) =================
def run_dino():
    GROUND_Y = 56
    dino_x = 12
    dino_y = GROUND_Y - 12
    velocity_y = 0.0
    is_jumping = False
    
    cactus_x = WIDTH + 10
    cactus_y = GROUND_Y - 11
    cactus_speed = 3.0
    
    score = 0
    high_score = 0
    game_over = False
    score_timer = time.ticks_ms()
    last_btn = 1

    def draw_d(x, y):
        y = int(y)
        oled.fill_rect(x + 4, y, 7, 4, 1)
        oled.fill_rect(x + 2, y + 4, 10, 5, 1)
        oled.fill_rect(x, y + 9, 4, 3, 1)
        oled.fill_rect(x + 7, y + 9, 3, 3, 1)
        oled.pixel(x + 9, y + 1, 0)

    def draw_c(x, y):
        oled.fill_rect(x + 2, y, 3, 11, 1)
        oled.fill_rect(x, y + 3, 2, 4, 1)
        oled.fill_rect(x + 5, y + 5, 2, 4, 1)

    while True:
        vl = btn_left.value()
        vr = btn_right.value()
        
        # 雙鍵同按 -> 回主選單
        if vl == 0 and vr == 0:
            time.sleep_ms(500)
            break

        btn_pressed = (last_btn == 1 and (vl == 0 or vr == 0))
        last_btn = 0 if (vl == 0 or vr == 0) else 1

        if not game_over:
            if btn_pressed and not is_jumping:
                beep_click(15)
                velocity_y = -6.5
                is_jumping = True

            if is_jumping:
                dino_y += velocity_y
                velocity_y += 0.9
                if dino_y >= GROUND_Y - 12:
                    dino_y = GROUND_Y - 12
                    velocity_y = 0.0
                    is_jumping = False

            cactus_x -= cactus_speed
            if cactus_x < -6:
                cactus_x = WIDTH + random.randint(15, 60)
                cactus_speed = min(6.0, 3.0 + (score // 10) * 0.5)

            now = time.ticks_ms()
            if time.ticks_diff(now, score_timer) > 250:
                score += 1
                score_timer = now

            # 碰撞檢測
            if (dino_x + 9 > cactus_x and dino_x + 2 < cactus_x + 6 and dino_y + 10 > cactus_y):
                game_over = True
                alarm_beep(1)
                if score > high_score:
                    high_score = score

            oled.fill(0)
            oled.hline(0, GROUND_Y, WIDTH, 1)
            oled.text(f"SCORE:{score:04d}", 0, 0, 1)
            oled.text(f"HI:{high_score:04d}", 72, 0, 1)
            draw_d(dino_x, dino_y)
            if cactus_x < WIDTH:
                draw_c(int(cactus_x), cactus_y)
            oled.show()
        else:
            oled.fill_rect(14, 14, 100, 36, 0)
            oled.rect(14, 14, 100, 36, 1)
            oled.text("GAME OVER!", 24, 18, 1)
            oled.text(f"SCORE: {score}", 30, 28, 1)
            oled.text("L/R:RESTART", 20, 38, 1)
            oled.show()

            if btn_pressed:
                beep_click(25)
                score = 0
                cactus_x = WIDTH + 10
                cactus_speed = 3.0
                dino_y = GROUND_Y - 12
                velocity_y = 0.0
                is_jumping = False
                game_over = False
                score_timer = time.ticks_ms()
                time.sleep_ms(200)

        time.sleep_ms(25)

# ================= 應用 2: 貓咪餐券 (Cat Voucher - 極致儀式感版) =================
def run_cat_voucher():
    tickets = 1
    
    def render_voucher():
        oled.fill(0)
        oled.fill_rect(0, 0, 128, 13, 1)
        oled.text("* CAT VOUCHER *", 8, 3, 0)
        oled.rect(8, 18, 112, 28, 1)
        oled.text("MEAL TICKET : 1", 12, 23, 1)
        oled.text("Feast For Kitty", 12, 34, 1)
        for x in range(12, 118, 6):
            oled.pixel(x, 29, 0)
        oled.hline(0, 50, 128, 1)
        oled.text("Hold R to TEAR!", 6, 54, 1)
        oled.show()

    def play_tear_animation():
        # 左右撕裂動畫 (細膩慢速裂開)
        for offset in range(0, 36, 2):
            oled.fill(0)
            oled.fill_rect(0, 0, 128, 13, 1)
            oled.text("* TEARING... *", 10, 3, 0)
            oled.rect(8 - offset, 20, 50, 26, 1)
            oled.text("MEAL", 12 - offset, 25, 1)
            oled.rect(64 + offset, 20, 56, 26, 1)
            oled.text("TICKET", 68 + offset, 25, 1)
            oled.show()
            time.sleep_ms(60)

        # 慢速療癒進食動畫 (延長至 5 輪循環，每幀 600ms 慢嚼細嚥)
        for cycle in range(5):
            oled.fill(0)
            oled.fill_rect(0, 0, 128, 12, 1)
            oled.text(f"FEAST TIME ({cycle+1}/5)", 10, 2, 0)
            oled.text(" (=^.^=) nyam! ", 6, 22, 1)
            oled.text("   >===<  FISH! ", 6, 40, 1)
            oled.show()
            time.sleep_ms(600)

            oled.fill(0)
            oled.fill_rect(0, 0, 128, 12, 1)
            oled.text(f"FEAST TIME ({cycle+1}/5)", 10, 2, 0)
            oled.text(" ( ^o^ ) yummy!", 6, 22, 1)
            oled.text("    )==(  CRUNCH", 6, 40, 1)
            oled.show()
            time.sleep_ms(600)

    render_voucher()
    while True:
        vl = btn_left.value()
        vr = btn_right.value()

        # 雙鍵同按 -> 回主選單
        if vl == 0 and vr == 0:
            time.sleep_ms(500)
            break

        # 右鍵長按蓄力撕票 (時間拉長至 3.0 秒，儀式感滿滿)
        TEAR_HOLD_SEC = 3.0
        if vr == 0 and tickets > 0:
            hold_start = time.time()
            torn = False
            while btn_right.value() == 0:
                dur = time.time() - hold_start
                pct = min(1.0, dur / TEAR_HOLD_SEC)
                oled.fill(0)
                oled.fill_rect(0, 0, 128, 13, 1)
                oled.text("[ TEARING TICKET ]", 0, 3, 0)
                oled.text(f"CHARGING: {int(pct*100)}%", 16, 20, 1)
                oled.rect(14, 34, 100, 9, 1)
                oled.fill_rect(16, 36, int(pct * 96), 5, 1)
                oled.text("DON'T LET GO!", 16, 48, 1)
                oled.show()
                if pct >= 1.0:
                    torn = True
                    break
                time.sleep_ms(40)

            if torn:
                tickets -= 1
                # 震動白閃提示
                for _ in range(2):
                    oled.fill(1)
                    oled.show()
                    time.sleep_ms(60)
                    oled.fill(0)
                    oled.show()
                    time.sleep_ms(60)
                play_tear_animation()
                
                # 吃飽飽大滿足畫面
                oled.fill(0)
                oled.fill_rect(0, 0, 128, 13, 1)
                oled.text("  TICKET USED   ", 8, 3, 0)
                oled.text(" (=^w^=) FULL! ", 8, 20, 1)
                oled.text("Cat is satisfied", 0, 35, 1)
                oled.text("L+R: Back Menu", 10, 52, 1)
                oled.show()
                while True:
                    if btn_left.value() == 0 and btn_right.value() == 0:
                        time.sleep_ms(500)
                        return
                    time.sleep_ms(30)
            else:
                render_voucher()

        time.sleep_ms(30)

# ================= 應用 3: 番茄鐘 (Pomodoro Focus) =================
def run_pomodoro():
    MODES = [
        {"name": "25m Focus", "secs": 25 * 60},
        {"name": "5m Break",  "secs": 5 * 60},
        {"name": "10s Test",  "secs": 10}
    ]
    mode_idx = 0
    time_left = MODES[mode_idx]["secs"]
    is_running = False
    last_tick = time.time()
    last_l = 1
    last_r = 1

    def render():
        oled.fill(0)
        oled.fill_rect(0, 0, 128, 13, 1)
        cur = MODES[mode_idx]
        oled.text(f"[ {cur['name']} ]", 4, 3, 0)
        
        mins = time_left // 60
        secs = time_left % 60
        oled.text(f">> {mins:02d}:{secs:02d} <<", 18, 20, 1)
        
        progress = max(0.0, min(1.0, 1.0 - (time_left / cur["secs"])))
        oled.rect(14, 34, 100, 7, 1)
        oled.fill_rect(16, 36, int(progress * 96), 3, 1)
        
        oled.hline(0, 48, 128, 1)
        if is_running:
            oled.text("R:Pause  L:Reset", 0, 52, 1)
        else:
            oled.text("L:Mode   R:Start", 0, 52, 1)
        oled.show()

    render()

    while True:
        vl = btn_left.value()
        vr = btn_right.value()

        # 雙鍵同按 -> 回主選單
        if vl == 0 and vr == 0:
            time.sleep_ms(500)
            break

        if is_running:
            now = time.time()
            if now != last_tick:
                time_left = max(0, time_left - (now - last_tick))
                last_tick = now
                render()
                if time_left == 0:
                    is_running = False
                    # 畫面閃爍並同步觸發蜂鳴器與內建 LED 爆閃鬧鐘提醒
                    for _ in range(3):
                        oled.fill(1)
                        oled.show()
                        buzzer.value(1)
                        led.value(1)
                        time.sleep_ms(120)
                        oled.fill(0)
                        oled.show()
                        buzzer.value(0)
                        led.value(0)
                        time.sleep_ms(80)
                    
                    oled.text("* POMODORO DONE *", 0, 24, 1)
                    oled.text("FOCUS SUCCESS!", 10, 40, 1)
                    oled.show()
                    # 結尾再來一次急促連響與閃爍提醒
                    alarm_beep(2)
                    time.sleep(1.5)
                    time_left = MODES[mode_idx]["secs"]
                    render()

        # L 鍵
        if last_l == 1 and vl == 0:
            beep_click(20)
            if is_running:
                is_running = False
                led.value(0)
                time_left = MODES[mode_idx]["secs"]
            else:
                mode_idx = (mode_idx + 1) % len(MODES)
                time_left = MODES[mode_idx]["secs"]
            render()
            time.sleep_ms(200)

        # R 鍵
        if last_r == 1 and vr == 0:
            beep_click(30)
            is_running = not is_running
            if not is_running:
                led.value(0)
            last_tick = time.time()
            render()
            time.sleep_ms(200)

        last_l = vl
        last_r = vr
        time.sleep_ms(30)

# ================= 應用 4: 極客時鐘與碼表 (Geek Clock & Stopwatch) =================
def run_clock():
    start_ms = time.ticks_ms()
    stopwatch_ms = 0
    sw_running = False
    sw_start = 0
    last_l = 1
    last_r = 1

    while True:
        vl = btn_left.value()
        vr = btn_right.value()

        # 雙鍵同按 -> 回主選單
        if vl == 0 and vr == 0:
            time.sleep_ms(500)
            break

        # L 鍵: 碼表歸零
        if last_l == 1 and vl == 0:
            beep_click(20)
            stopwatch_ms = 0
            if sw_running:
                sw_start = time.ticks_ms()
            time.sleep_ms(200)

        # R 鍵: 碼表 啟動 / 暫停
        if last_r == 1 and vr == 0:
            beep_click(30)
            sw_running = not sw_running
            if sw_running:
                sw_start = time.ticks_ms() - stopwatch_ms
            time.sleep_ms(200)

        if sw_running:
            stopwatch_ms = time.ticks_diff(time.ticks_ms(), sw_start)

        # 系統累計運行時間 (Uptime)
        uptime_sec = time.ticks_diff(time.ticks_ms(), start_ms) // 1000
        up_m = uptime_sec // 60
        up_s = uptime_sec % 60

        # 碼表時間
        sw_sec = stopwatch_ms // 1000
        sw_d = (stopwatch_ms % 1000) // 100

        oled.fill(0)
        oled.fill_rect(0, 0, 128, 13, 1)
        oled.text("[ GEEK CLOCK ]", 8, 3, 0)
        
        oled.text(f"UPTIME:  {up_m:02d}:{up_s:02d}", 8, 20, 1)
        oled.text(f"STOPW: {sw_sec//60:02d}:{sw_sec%60:02d}.{sw_d}", 8, 34, 1)
        
        oled.hline(0, 48, 128, 1)
        sw_tag = "Pause" if sw_running else "Start"
        oled.text(f"L:Zero   R:{sw_tag}", 0, 52, 1)
        oled.show()

        last_l = vl
        last_r = vr
        time.sleep_ms(50)

# ================= 主流程進入點 =================
def main():
    gc.collect()
    play_boot_ceremony()
    
    while True:
        gc.collect()
        choice = show_main_menu()
        if choice == 0:
            run_dino()
        elif choice == 1:
            run_cat_voucher()
        elif choice == 2:
            run_pomodoro()
        elif choice == 3:
            run_clock()

if __name__ == "__main__":
    main()
