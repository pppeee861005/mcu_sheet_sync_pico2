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

WIDTH = 128
HEIGHT = 64

i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=400000)
oled = SSD1306_I2C(WIDTH, HEIGHT, i2c)

btn_left = Pin(BUTTON_LEFT_PIN, Pin.IN, Pin.PULL_UP)
btn_right = Pin(BUTTON_RIGHT_PIN, Pin.IN, Pin.PULL_UP)

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

# ================= 3. 主選單 (7 大應用) =================
MENU_ITEMS = [
    {"title": "1. DINO GAME",  "desc": "Jump & Dodge"},
    {"title": "2. RACING GAME","desc": "Formula Turbo"},
    {"title": "3. POKEMON BATTLE","desc": "Pikachu vs Eevee"},
    {"title": "4. TAMAGOTCHI", "desc": "Virtual Pet Care"},
    {"title": "5. CAT VOUCHER","desc": "Tear & Feast"},
    {"title": "6. POMODORO",   "desc": "Focus Timer"},
    {"title": "7. GEEK CLOCK", "desc": "Stopwatch & Time"}
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
            selected = (selected + 1) % len(MENU_ITEMS)
            render()
            time.sleep_ms(200)

        if last_r == 1 and vr == 0:
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

# ================= 應用 2: 極速賽車 (Retro Racing 8-Bit) =================
def run_racing():
    ROAD_L = 20
    ROAD_R = 108
    ROAD_W = ROAD_R - ROAD_L
    LANES = [ROAD_L + 12, ROAD_L + int(ROAD_W * 0.5), ROAD_R - 12] # 左、中、右三線道

    player_lane = 1      # 預設中間車道
    player_y = 48        # 玩家車輛固定底部
    car_w = 12
    car_h = 14

    # 敵車 (障礙車輛)
    enemies = []
    
    score = 0
    speed = 4.0
    game_over = False
    road_dash_offset = 0

    last_l = 1
    last_r = 1

    def draw_f1_car(x, y, is_player=True):
        """繪製精緻的 8-Bit 方程式賽車點陣"""
        x = int(x - car_w // 2)
        y = int(y)
        # 車身主體
        oled.fill_rect(x + 4, y, 4, car_h, 1)
        # 車頭翼板
        oled.fill_rect(x + 2, y + 1, 8, 2, 1)
        # 駕駛艙座
        oled.pixel(x + 5, y + 5, 0 if is_player else 1)
        oled.pixel(x + 6, y + 5, 0 if is_player else 1)
        # 前輪 (左/右)
        oled.fill_rect(x, y + 2, 2, 3, 1)
        oled.fill_rect(x + 10, y + 2, 2, 3, 1)
        # 後輪 (左/右，較寬)
        oled.fill_rect(x, y + car_h - 4, 3, 4, 1)
        oled.fill_rect(x + 9, y + car_h - 4, 3, 4, 1)
        # 尾翼
        oled.fill_rect(x + 2, y + car_h - 2, 8, 2, 1)

    while True:
        vl = btn_left.value()
        vr = btn_right.value()

        # 雙鍵同按 -> 回主選單
        if vl == 0 and vr == 0:
            time.sleep_ms(500)
            break

        # 左鍵 (GPIO 18): 車子往左車道變換
        if last_l == 1 and vl == 0 and not game_over:
            if player_lane > 0:
                player_lane -= 1
            time.sleep_ms(100)

        # 右鍵 (GPIO 4): 車子往右車道變換
        if last_r == 1 and vr == 0 and not game_over:
            if player_lane < len(LANES) - 1:
                player_lane += 1
            time.sleep_ms(100)

        last_l = vl
        last_r = vr

        if not game_over:
            # 道路虛線向下捲動效果
            road_dash_offset = (road_dash_offset + int(speed)) % 16

            # 隨機產生敵車
            if len(enemies) == 0 or (enemies[-1]["y"] > 24 and random.random() < 0.25):
                lane_choice = random.randint(0, len(LANES) - 1)
                enemies.append({"lane": lane_choice, "y": -car_h})

            # 更新敵車位置與計分
            for e in enemies:
                e["y"] += speed

            # 超車得分
            if enemies and enemies[0]["y"] > HEIGHT:
                enemies.pop(0)
                score += 1
                # 速度漸進提升
                speed = min(9.0, 4.0 + (score // 5) * 0.5)

            # 碰撞檢測
            p_center_x = LANES[player_lane]
            for e in enemies:
                e_center_x = LANES[e["lane"]]
                # 檢查車道重疊與 Y 軸距離
                if e["lane"] == player_lane and (e["y"] + car_h > player_y and e["y"] < player_y + car_h):
                    game_over = True
                    break

            # 繪製畫面
            oled.fill(0)

            # 賽道左右邊界護欄 (實線 + 斑馬外緣)
            oled.vline(ROAD_L, 0, HEIGHT, 1)
            oled.vline(ROAD_R, 0, HEIGHT, 1)
            for gy in range(0, HEIGHT, 8):
                oled.pixel(ROAD_L - 2, gy, 1)
                oled.pixel(ROAD_R + 2, gy, 1)

            # 賽道中間雙虛線
            lane_w = ROAD_W // 3
            dash_x1 = ROAD_L + lane_w
            dash_x2 = ROAD_L + lane_w * 2
            for dy in range(-16 + road_dash_offset, HEIGHT, 16):
                oled.fill_rect(dash_x1, dy, 1, 8, 1)
                oled.fill_rect(dash_x2, dy, 1, 8, 1)

            # 繪製敵車
            for e in enemies:
                if e["y"] > -car_h and e["y"] < HEIGHT:
                    draw_f1_car(LANES[e["lane"]], e["y"], is_player=False)

            # 繪製玩家賽車
            draw_f1_car(LANES[player_lane], player_y, is_player=True)

            # 左側垂直顯示分數與檔位
            oled.text(f"S", 2, 4, 1)
            oled.text(f"{score//10}", 2, 16, 1)
            oled.text(f"{score%10}", 2, 26, 1)
            oled.text("KM", 112, 10, 1)
            oled.text(f"{int(speed*20)}", 112, 22, 1)

            oled.show()

        else:
            # 撞車 Game Over
            oled.fill_rect(16, 14, 96, 36, 0)
            oled.rect(16, 14, 96, 36, 1)
            oled.text("CRASHED!", 32, 18, 1)
            oled.text(f"SCORE: {score}", 30, 28, 1)
            oled.text("L/R:RESTART", 20, 38, 1)
            oled.show()

            if (last_l == 1 and vl == 0) or (last_r == 1 and vr == 0):
                score = 0
                speed = 4.0
                enemies = []
                player_lane = 1
                game_over = False
                time.sleep_ms(200)

        time.sleep_ms(30)

# ================= 應用 3: 寶可夢經典對戰 (Pokemon Battle: Pikachu vs Eevee) =================
def run_pokemon():
    p_max_hp = 30
    p_hp = p_max_hp
    e_max_hp = 28
    e_hp = e_max_hp

    # 技能清單 (名字, 傷害, 命中率, 說明)
    MOVES = [
        {"name": "THUNDERBOLT", "dmg": 10, "acc": 85},
        {"name": "QUICK ATTACK", "dmg": 6,  "acc": 100},
        {"name": "IRON TAIL",    "dmg": 12, "acc": 70},
        {"name": "POTION",       "dmg": -12, "acc": 100} # 補血
    ]
    cur_move = 0
    state = "CHOOSE" # CHOOSE, ANIM, ENEMY_TURN, WIN, LOSE
    anim_text = ""
    last_l = 1
    last_r = 1

    def draw_hp_bar(x, y, cur, max_val):
        oled.rect(x, y, 38, 5, 1)
        fill_w = int(max(0.0, min(1.0, cur / max_val)) * 36)
        if fill_w > 0:
            oled.fill_rect(x + 1, y + 1, fill_w, 3, 1)

    def draw_battle_scene(show_box=True):
        oled.fill(0)
        # 1. 敵方 (伊布 EEVEE - 右上方)
        oled.text("EEVEE Lv5", 58, 2, 1)
        draw_hp_bar(80, 11, e_hp, e_max_hp)
        oled.text("HP", 66, 10, 1)
        # 伊布簡易像素剪影 (耳朵 + 臉)
        oled.fill_rect(100, 18, 12, 10, 1)
        oled.fill_rect(96, 14, 4, 8, 1)   # 左耳
        oled.fill_rect(112, 14, 4, 8, 1)  # 右耳
        oled.pixel(103, 21, 0)
        oled.pixel(108, 21, 0)

        # 2. 我方 (皮卡丘 PIKACHU - 左下方後背視角)
        oled.text("PIKA Lv5", 2, 28, 1)
        draw_hp_bar(20, 37, p_hp, p_max_hp)
        oled.text("HP", 6, 36, 1)
        oled.text(f"{p_hp}/{p_max_hp}", 20, 43, 1)
        # 皮卡丘背影 + 閃電尾巴
        oled.fill_rect(6, 48, 14, 15, 1)
        oled.fill_rect(4, 52, 3, 6, 1)
        oled.fill_rect(19, 44, 4, 8, 1)  # 閃電尾巴折角
        oled.fill_rect(15, 48, 4, 4, 1)

        # 3. 底部指令或對話框
        if show_box:
            oled.rect(0, 52, 128, 12, 1)
            if state == "CHOOSE":
                # 顯示選中招式與換招提示
                m_name = MOVES[cur_move]["name"]
                oled.text(f">{m_name[:8]} L:Chg R:Atk"[:16], 2, 54, 1)
            else:
                oled.text(anim_text[:16], 4, 54, 1)
        oled.show()

    draw_battle_scene()

    while True:
        vl = btn_left.value()
        vr = btn_right.value()

        # 雙鍵同按 -> 回主選單
        if vl == 0 and vr == 0:
            time.sleep_ms(500)
            break

        # 玩家回合：選擇招式
        if state == "CHOOSE":
            # 左鍵 (GPIO 18): 切換招式
            if last_l == 1 and vl == 0:
                cur_move = (cur_move + 1) % len(MOVES)
                draw_battle_scene()
                time.sleep_ms(150)

            # 右鍵 (GPIO 4): 確認出招
            if last_r == 1 and vr == 0:
                move = MOVES[cur_move]
                state = "ANIM"
                
                # 判定補血或攻擊
                if move["dmg"] < 0:
                    p_hp = min(p_max_hp, p_hp - move["dmg"])
                    anim_text = "Pika uses POTION!"
                else:
                    hit = random.randint(1, 100) <= move["acc"]
                    if hit:
                        e_hp = max(0, e_hp - move["dmg"])
                        anim_text = f"Pika {move['name'][:7]}!"
                    else:
                        anim_text = "Attack Missed!"

                draw_battle_scene()
                time.sleep(1.2)

                # 閃爍特效
                for _ in range(2):
                    draw_battle_scene(show_box=False)
                    time.sleep_ms(60)
                    oled.invert(True)
                    time.sleep_ms(60)
                    oled.invert(False)

                if e_hp == 0:
                    state = "WIN"
                    anim_text = "EEVEE Fainted!"
                    draw_battle_scene()
                    time.sleep(1.5)
                    anim_text = "YOU WIN! L/R:Re"
                    draw_battle_scene()
                else:
                    # 輪到敵方回合
                    state = "ENEMY_TURN"
                    anim_text = "Eevee attacks!"
                    draw_battle_scene()
                    time.sleep(1.0)
                    
                    # 伊布反擊
                    e_dmg = random.choice([5, 8, 10])
                    p_hp = max(0, p_hp - e_dmg)
                    anim_text = f"Bite! -{e_dmg} HP"
                    draw_battle_scene()
                    time.sleep(1.2)

                    if p_hp == 0:
                        state = "LOSE"
                        anim_text = "Pikachu Fainted!"
                        draw_battle_scene()
                        time.sleep(1.5)
                        anim_text = "GAME OVER L/R:Re"
                        draw_battle_scene()
                    else:
                        state = "CHOOSE"
                        draw_battle_scene()

                time.sleep_ms(100)

        elif state in ["WIN", "LOSE"]:
            # 結算重玩
            if (last_l == 1 and vl == 0) or (last_r == 1 and vr == 0):
                p_hp = p_max_hp
                e_hp = e_max_hp
                cur_move = 0
                state = "CHOOSE"
                draw_battle_scene()
                time.sleep_ms(200)

        last_l = vl
        last_r = vr
        time.sleep_ms(30)

# ================= 應用 4: 拓麻歌子經典電子寵物 (Tamagotchi Pet) =================
def run_tamagotchi():
    hunger = 4       # 飽足感 (0~5 顆心)
    happy = 4        # 快樂值 (0~5 顆心)
    poop_count = 0   # 便便數量
    is_sleeping = False
    
    pet_actions = ["FEED", "PLAY", "CLEAN", "SLEEP"]
    cur_act = 0
    
    anim_frame = 0
    last_tick = time.time()
    last_l = 1
    last_r = 1

    def draw_hearts(x, y, count):
        for i in range(5):
            if i < count:
                oled.fill_rect(x + i * 8, y + 1, 5, 4, 1)
                oled.pixel(x + i * 8 + 2, y + 4, 1)
            else:
                oled.rect(x + i * 8, y + 1, 5, 4, 1)

    def draw_pet(x, y, frame):
        """繪製經典像素小怪獸電子寵物 (左右蹦跳動畫)"""
        # 睡覺狀態
        if is_sleeping:
            oled.fill_rect(x, y + 6, 20, 10, 1)
            oled.text("Zzz", x + 18, y - 4, 1)
            return

        # 正常站立 / 歡呼幀
        bounce = 2 if frame % 2 == 1 else 0
        # 身體 (圓滾滾)
        oled.fill_rect(x + 2, y + bounce, 16, 14, 1)
        oled.fill_rect(x, y + 3 + bounce, 20, 8, 1)
        # 眼睛 (閃爍)
        oled.pixel(x + 5, y + 5 + bounce, 0)
        oled.pixel(x + 14, y + 5 + bounce, 0)
        # 嘴巴 (笑臉)
        oled.pixel(x + 9, y + 9 + bounce, 0)
        oled.pixel(x + 10, y + 9 + bounce, 0)
        # 耳朵
        oled.fill_rect(x + 3, y - 3 + bounce, 3, 3, 1)
        oled.fill_rect(x + 14, y - 3 + bounce, 3, 3, 1)
        # 小腳丫
        if frame % 2 == 0:
            oled.fill_rect(x + 4, y + 14, 3, 2, 1)
            oled.fill_rect(x + 13, y + 14, 3, 2, 1)
        else:
            oled.fill_rect(x + 2, y + 13, 3, 2, 1)
            oled.fill_rect(x + 15, y + 13, 3, 2, 1)

    def draw_poop(x, y):
        """繪製一坨可愛的便便"""
        oled.fill_rect(x + 2, y, 4, 2, 1)
        oled.fill_rect(x + 1, y + 2, 6, 2, 1)
        oled.fill_rect(x, y + 4, 8, 3, 1)

    def render_screen():
        oled.fill(0)
        # 頂部狀態列 (HUNGER & HAPPY 心心)
        oled.text("F:", 2, 2, 1)
        draw_hearts(18, 2, hunger)
        oled.text("H:", 66, 2, 1)
        draw_hearts(82, 2, happy)
        oled.hline(0, 11, 128, 1)

        # 中間主畫面 (寵物 + 便便)
        pet_x = 54
        pet_y = 22
        draw_pet(pet_x, pet_y, anim_frame)

        if poop_count > 0:
            draw_poop(96, 32)
            if poop_count > 1:
                draw_poop(108, 32)

        # 底部動作選單
        oled.hline(0, 48, 128, 1)
        act_name = pet_actions[cur_act]
        oled.text(f">{act_name}  L:Chg R:Do"[:16], 2, 52, 1)
        oled.show()

    render_screen()

    while True:
        vl = btn_left.value()
        vr = btn_right.value()

        # 雙鍵同按 -> 回主選單
        if vl == 0 and vr == 0:
            time.sleep_ms(500)
            break

        # 時間自然流逝 (每 15 秒飢餓度扣 1，有機率大便)
        now = time.time()
        if now - last_tick > 12:
            last_tick = now
            if not is_sleeping:
                hunger = max(0, hunger - 1)
                happy = max(0, happy - 1)
                if hunger <= 1 or poop_count > 0:
                    happy = max(0, happy - 1)
                if random.random() < 0.4 and poop_count < 2:
                    poop_count += 1
            render_screen()

        # 動畫跳動循環
        anim_frame = (anim_frame + 1) % 2

        # 左鍵 (GPIO 18): 切換操作動作 (FEED / PLAY / CLEAN / SLEEP)
        if last_l == 1 and vl == 0:
            cur_act = (cur_act + 1) % len(pet_actions)
            render_screen()
            time.sleep_ms(150)

        # 右鍵 (GPIO 4): 執行選中的動作
        if last_r == 1 and vr == 0:
            act = pet_actions[cur_act]
            if act == "FEED":
                if hunger < 5:
                    hunger = min(5, hunger + 2)
                    oled.fill(0)
                    oled.text("FEEDING CAKE!", 16, 20, 1)
                    oled.text("(=^O^=) DELICIOUS", 2, 38, 1)
                    oled.show()
                    time.sleep(1.2)
            elif act == "PLAY":
                if not is_sleeping:
                    happy = min(5, happy + 2)
                    oled.fill(0)
                    oled.text("PLAYING BALL!", 16, 20, 1)
                    oled.text("(\\^o^/) YAY HAPPY", 0, 38, 1)
                    oled.show()
                    time.sleep(1.2)
            elif act == "CLEAN":
                if poop_count > 0:
                    poop_count = 0
                    happy = min(5, happy + 1)
                    oled.fill(0)
                    oled.text("CLEANING POOP!", 10, 20, 1)
                    oled.text("* SPARKLE CLEAN *", 0, 38, 1)
                    oled.show()
                    time.sleep(1.2)
            elif act == "SLEEP":
                is_sleeping = not is_sleeping
                oled.fill(0)
                txt = "LIGHTS OFF Zzz" if is_sleeping else "WAKE UP SUNNY!"
                oled.text(txt, 12, 28, 1)
                oled.show()
                time.sleep(1.0)

            render_screen()
            time.sleep_ms(150)

        last_l = vl
        last_r = vr
        render_screen()
        time.sleep_ms(400)

# ================= 應用 5: 貓咪餐券 (Cat Voucher - 極致儀式感版) =================
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
                    for _ in range(3):
                        oled.fill(1)
                        oled.show()
                        time.sleep_ms(100)
                        oled.fill(0)
                        oled.show()
                        time.sleep_ms(100)
                    oled.text("* POMODORO DONE *", 0, 24, 1)
                    oled.text("FOCUS SUCCESS!", 10, 40, 1)
                    oled.show()
                    time.sleep(2)
                    time_left = MODES[mode_idx]["secs"]
                    render()

        # L 鍵
        if last_l == 1 and vl == 0:
            if is_running:
                is_running = False
                time_left = MODES[mode_idx]["secs"]
            else:
                mode_idx = (mode_idx + 1) % len(MODES)
                time_left = MODES[mode_idx]["secs"]
            render()
            time.sleep_ms(200)

        # R 鍵
        if last_r == 1 and vr == 0:
            is_running = not is_running
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
            stopwatch_ms = 0
            if sw_running:
                sw_start = time.ticks_ms()
            time.sleep_ms(200)

        # R 鍵: 碼表 啟動 / 暫停
        if last_r == 1 and vr == 0:
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
            run_racing()
        elif choice == 2:
            run_pokemon()
        elif choice == 3:
            run_tamagotchi()
        elif choice == 4:
            run_cat_voucher()
        elif choice == 5:
            run_pomodoro()
        elif choice == 6:
            run_clock()

if __name__ == "__main__":
    main()
