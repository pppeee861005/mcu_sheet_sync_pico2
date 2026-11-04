# main.py - Pico 2 W 儀式感雙系統韌體 (Pull 只拉取最新文字版)
# 系統 1: Sheet Sync (上報同步)
# 系統 2: CloudMsg 看板 (純 Pull 最新文字 / 支援超長文字跑馬燈捲動，絕不傳送任何資料)

import time
import network
import socket
import ssl
import json
import gc
from machine import Pin, I2C
from pico_i2c_lcd import I2cLcd
from config import WIFI_NETWORKS, GAS_SCRIPT_ID, GOOGLE_API_KEY

# ================= 1. 硬體初始化 =================
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=100000)
devices = i2c.scan()
if not devices:
    raise SystemExit
addr = devices[0]
lcd = I2cLcd(i2c, addr, 2, 16)
lcd.clear()

btn_left = Pin(14, Pin.IN, Pin.PULL_UP)   # GP14: Left / Next / Action 1
btn_right = Pin(16, Pin.IN, Pin.PULL_UP)  # GP16: Right / Enter / Action 2

def lcd_p(l0="", l1=""):
    lcd.move_to(0, 0)
    lcd.putstr(f"{l0:<16}"[:16])
    lcd.move_to(0, 1)
    lcd.putstr(f"{l1:<16}"[:16])

# ================= 2. 開機儀式感動畫 =================
def play_ceremony():
    lcd.clear()
    for i in range(1, 9):
        lcd.move_to(8 - i, 0)
        lcd.putstr(">" * i)
        lcd.move_to(8, 0)
        lcd.putstr("<" * i)
        time.sleep_ms(35)
    time.sleep_ms(120)
    lcd.clear()
    lcd_p("* PICO 2 W OS *", "[              ]")
    for p in range(14):
        lcd.move_to(1 + p, 1)
        lcd.putstr("=")
        time.sleep_ms(40)
    lcd_p("* PICO 2 W OS *", " WELCOME, MAKER!")
    time.sleep(1.2)

# ================= 3. 原生輕量防碎片 HTTPS 核心 =================
def safe_gas_request(params="", payload=None, timeout=10):
    gc.collect()
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        return None, "Offline"

    host = "script.google.com"
    path = f"/macros/s/{GAS_SCRIPT_ID}/exec"
    if params:
        path += f"?{params}"

    s = None
    ss = None
    loc = None

    try:
        ai = socket.getaddrinfo(host, 443)
        s = socket.socket()
        s.settimeout(timeout)
        s.connect(ai[0][-1])
        ss = ssl.wrap_socket(s, server_hostname=host)
        
        method = "POST" if payload else "GET"
        body_data = json.dumps(payload) if payload else ""
        h_len = f"Content-Length: {len(body_data)}\r\n" if payload else ""
        h_type = "Content-Type: application/json\r\n" if payload else ""
        
        req = f"{method} {path} HTTP/1.0\r\nHost: {host}\r\nConnection: close\r\nUser-Agent: Pico2W\r\n{h_type}{h_len}\r\n{body_data}"
        ss.write(req.encode())
        
        while True:
            line = ss.readline()
            if not line or line == b"\r\n":
                break
            if line.lower().startswith(b"location:"):
                loc = line[9:].strip().decode()
    except Exception as e:
        return None, "Stage1_Err"
    finally:
        if ss:
            try: ss.close()
            except: pass
        if s:
            try: s.close()
            except: pass
        gc.collect()

    if not loc:
        return None, "No_Loc"

    # Stage 2: 重新導向目標取得資料
    s2 = None
    ss2 = None
    try:
        _, _, host_path = loc.partition("://")
        r_host, _, r_path = host_path.partition("/")
        ai2 = socket.getaddrinfo(r_host, 443)
        s2 = socket.socket()
        s2.settimeout(timeout)
        s2.connect(ai2[0][-1])
        ss2 = ssl.wrap_socket(s2, server_hostname=r_host)
        
        req2 = f"GET /{r_path} HTTP/1.0\r\nHost: {r_host}\r\nConnection: close\r\nUser-Agent: Pico2W\r\n\r\n"
        ss2.write(req2.encode())
        
        while True:
            line = ss2.readline()
            if not line or line == b"\r\n":
                break
        body = ss2.read()
        if body:
            try:
                return json.loads(body.decode()), "OK"
            except:
                return body.decode(), "OK"
        return None, "Empty"
    except Exception as e:
        return None, "Stage2_Err"
    finally:
        if ss2:
            try: ss2.close()
            except: pass
        if s2:
            try: s2.close()
            except: pass
        gc.collect()

def call_gemini_flash(prompt_text, timeout=25):
    """
    輕量呼叫 Google Gemini 2.5 Flash REST API (MicroPython 原生 socket + ssl)
    """
    gc.collect()
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        return None, "Offline"

    host = "generativelanguage.googleapis.com"
    path = f"/v1beta/models/gemini-3.5-flash:generateContent?key={GOOGLE_API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt_text}]
        }],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 100
        }
    }
    
    body_data = json.dumps(payload)
    s = None
    ss = None
    
    try:
        ai = socket.getaddrinfo(host, 443)
        s = socket.socket()
        s.settimeout(timeout)
        s.connect(ai[0][-1])
        ss = ssl.wrap_socket(s, server_hostname=host)
        
        req = (
            f"POST {path} HTTP/1.0\r\n"
            f"Host: {host}\r\n"
            f"User-Agent: Pico2W\r\n"
            f"Content-Type: application/json\r\n"
            f"Content-Length: {len(body_data)}\r\n"
            f"Connection: close\r\n\r\n"
            f"{body_data}"
        )
        ss.write(req.encode())
        
        # 讀取 HTTP Header
        while True:
            line = ss.readline()
            if not line or line == b"\r\n":
                break
                
        # 讀取 Response Body
        resp_bytes = ss.read()
        if not resp_bytes:
            return None, "Empty_Resp"
            
        data = json.loads(resp_bytes.decode())
        if "candidates" in data and len(data["candidates"]) > 0:
            text_out = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            return text_out, "OK"
        return None, "No_Candidates"
    except Exception as e:
        return None, "Gemini_Err"
    finally:
        if ss:
            try: ss.close()
            except: pass
        if s:
            try: s.close()
            except: pass
        gc.collect()

# ================= 4. 開機自動連線 Wi-Fi =================
def auto_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    for net in WIFI_NETWORKS:
        ssid = net["ssid"]
        pwd = net["password"]
        lcd_p("WiFi Connecting:", ssid[:16])
        wlan.connect(ssid, pwd)
        t0 = time.time()
        dot = 0
        while not wlan.isconnected() and (time.time() - t0 < 8):
            dot = (dot + 1) % 4
            lcd.move_to(0, 1)
            lcd.putstr(f"Linking{'.' * dot:<9}")
            time.sleep_ms(300)
            
        if wlan.isconnected():
            ip = wlan.ifconfig()[0]
            lcd_p("WiFi Connected!", ip[:16])
            time.sleep(1.2)
            return True
            
    lcd_p("WiFi Offline!", "Check Hotspot")
    time.sleep(1.2)
    return False

# ================= 5. 主選單 =================
SYSTEMS = [
    {"name": "1.Fortune Dice", "desc": "Lunch & Fate"},
    {"name": "2.CloudMsg",     "desc": "L:Pull   R:Push"},
    {"name": "3.Sheet Sync",   "desc": "Push Counter"},
    {"name": "4.AI Agri",      "desc": "Irrigate Inference"}
]

def main_menu():
    selected = 0
    last_l = 1
    last_r = 1

    def render_menu():
        lcd_p(f"> {SYSTEMS[selected]['name']}", f"L:Next   R:Enter")

    render_menu()

    while True:
        vl = btn_left.value()
        vr = btn_right.value()

        if last_l == 1 and vl == 0:
            selected = (selected + 1) % len(SYSTEMS)
            render_menu()
            time.sleep_ms(200)

        if last_r == 1 and vr == 0:
            time.sleep_ms(200)
            return selected

        last_l = vl
        last_r = vr
        time.sleep_ms(20)

# ================= 6. 系統 1: 雲端命運籤筒與午餐選擇機 (Fortune & Lunch Dice) =================
# 預設午餐與命運籤詩清單 (當雲端離線或抽籤時輪播用)
FORTUNE_OPTIONS = [
    "Beef Noodles",     # 牛肉麵
    "Pork Bento",       # 排骨便當
    "McDonald's",       # 麥當勞
    "Ramen & Gyoza",    # 拉麵煎餃
    "Bubble Tea Time",  # 珍奶時刻
    "Curry Rice",       # 咖哩飯
    "Subway Healthy",   # 潛艇堡
    "Fried Chicken",    # 炸雞大餐
    "Sushi Feast",      # 壽司生魚片
    "Dine with Cat!",   # 陪貓貓吃飯
    "Great Luck Day!",  # 大吉上上籤
    "Pizza Party!"      # 披薩大餐
]

def run_sys_fortune():
    lcd_p("[Fortune Dice]", "L:Preset R:Cloud")
    last_l = 1
    last_r = 1

    def roll_dice_animation(category="Lunch", options_list=FORTUNE_OPTIONS):
        if not options_list:
            options_list = FORTUNE_OPTIONS
            
        # ── 階段 1：神秘水晶球能量匯聚 (Occult Energy Charging) ──
        lcd.clear()
        # 兩側向中央收束的能量符文
        runes = [".", "+", "*", "#", "@"]
        for r_char in runes:
            lcd.move_to(0, 0)
            lcd.putstr(f" {r_char*3} ORACLE {r_char*3} "[:16].center(16))
            lcd.move_to(0, 1)
            lcd.putstr("CHARGING SOUL..."[:16].center(16))
            time.sleep_ms(180)

        # 背光心跳呼吸 (彷彿神諭降臨的閃爍)
        for _ in range(2):
            lcd.hal_backlight_off()
            time.sleep_ms(120)
            lcd.hal_backlight_on()
            time.sleep_ms(150)

        # ── 階段 2：命運齒輪瘋狂轉動 (Fate Gears Spinning) ──
        # 隨機符號漩渦預熱
        mystic_symbols = [" / ", " - ", " \\ ", " | "]
        for s in mystic_symbols * 2:
            lcd.move_to(0, 0)
            lcd.putstr(f"FATE AWAKENING {s}")
            lcd.move_to(0, 1)
            lcd.putstr(">> ?? ?? ?? <<".center(16))
            time.sleep_ms(90)

        # 由極速減速至定格 (拉霸命運減速)
        delays = [40, 40, 50, 60, 80, 110, 150, 210, 300, 450, 650]
        chosen = options_list[0]
        
        for idx, d in enumerate(delays):
            chosen = options_list[(time.ticks_ms() + idx) % len(options_list)]
            lcd.move_to(0, 0)
            lcd.putstr("= DECIDING FATE ="[:16].center(16))
            lcd.move_to(0, 1)
            # 伴隨左右括弧逼近鎖定
            lcd.putstr(f"> {chosen[:12]} <"[:16].center(16))
            time.sleep_ms(d)

        # ── 階段 3：神諭降臨 (The Revelation / Holy Light) ──
        # 莊嚴的背光三連閃 (神聖揭曉)
        for _ in range(3):
            lcd.hal_backlight_off()
            time.sleep_ms(100)
            lcd.hal_backlight_on()
            time.sleep_ms(100)

        lcd.clear()
        lcd.move_to(0, 0)
        lcd.putstr("*** ORACLE SAYS ***"[:16].center(16))
        lcd.move_to(0, 1)
        lcd.putstr(f">> {chosen[:10]} <<"[:16].center(16))
        time.sleep(2.2)

        # ── 階段 4：銘刻命運於雲端試算表 (Engrave to Cloud) ──
        lcd_p("Engraving Fate..", "Into Holy Sheet.")
        payload = {
            "action": "log_event",
            "device": "Pico2W",
            "event": "Mystic_Oracle",
            "message": f"Fate: {chosen}",
            "ts": time.time()
        }
        res, code = safe_gas_request(payload=payload)
        if code == "OK":
            lcd_p("Fate Inscribed!", chosen[:16])
        else:
            lcd_p("Oracle Sealed!", chosen[:16])
        time.sleep(2.0)

        lcd_p(f"Fate:{chosen[:11]}", "L:Preset R:Cloud")

    def handle_cloud_choice():
        """從 Google 試算表抓取逗號隔開的多個選項並隨機挑選一個"""
        lcd_p("Reading Sheet...", "Fetching items..")
        res, code = safe_gas_request(params="action=get_msg")
        
        items = []
        if code == "OK":
            raw_text = ""
            if isinstance(res, dict):
                raw_text = str(res.get("message") or res.get("msg") or "")
            else:
                raw_text = str(res)
                
            # 支援逗號 (英半形 , 或中全形 ，) 與空格切分
            if raw_text:
                # 替換中文逗號為英文逗號
                normalized = raw_text.replace("，", ",")
                items = [x.strip() for x in normalized.split(",") if x.strip()]

        if items:
            lcd_p("Loaded Options:", f"{len(items)} choices!")
            time.sleep(1.2)
            roll_dice_animation("Sheet", items)
        else:
            lcd_p("No Items Found!", "Using Presets...")
            time.sleep(1.5)
            roll_dice_animation("Lunch", FORTUNE_OPTIONS)

    while True:
        vl = btn_left.value()
        vr = btn_right.value()

        # 左鍵 (GP14): 抽本機預設籤筒 (Preset)
        if last_l == 1 and vl == 0:
            roll_dice_animation("Preset", FORTUNE_OPTIONS)
            time.sleep_ms(200)

        # 右鍵 (GP16): 從 Google Sheet 抓取自訂多選一清單 (Cloud Choice)
        if last_r == 1 and vr == 0:
            handle_cloud_choice()
            time.sleep_ms(200)

        last_l = vl
        last_r = vr
        time.sleep_ms(20)

# ================= 7. 系統 2: Sheet Sync (上報同步) =================
def run_sys_sync():
    count = 0
    lcd_p("[1] Sheet Sync", f"L:+1  R:Push [{count}]")
    last_l = 1
    last_r = 1

    while True:
        vl = btn_left.value()
        vr = btn_right.value()

        # GP14: +1
        if last_l == 1 and vl == 0:
            count += 1
            lcd_p("[1] Sheet Sync", f"L:+1  R:Push [{count}]")
            time.sleep_ms(150)

        # GP16: Push 上傳
        if last_r == 1 and vr == 0:
            lcd_p("Pushing Sheet...", f"Count: {count}")
            payload = {"action": "log_event", "device": "Pico2W", "count": count, "ts": time.time()}
            res, code = safe_gas_request(payload=payload)
            if code == "OK":
                lcd_p("Push Success!", f"Count {count} Saved")
            else:
                lcd_p("Push Failed!", code[:16])
            time.sleep(1.5)
            lcd_p("[1] Sheet Sync", f"L:+1  R:Push [{count}]")

        last_l = vl
        last_r = vr
        time.sleep_ms(20)

# ================= 7. 系統 2: CloudMsg (L:Pull 讀取最新留言 / R:Push 隨機英文字句) =================
# 內建精選隨機極客英文字句庫
RANDOM_MESSAGES = [
    "Stay Hungry Stay Foolish",
    "Keep Calm and Code On",
    "Hello from Pico 2 W!",
    "IoT is Magic with Code",
    "All Systems Nominal",
    "Time to Drink Coffee!",
    "Maker Spirit Never Dies",
    "Sync Cloud Complete!",
    "MicroPython is Great!",
    "Hack the Real World"
]

def run_sys_msg():
    board_msg = "Press L to Pull"
    lcd_p(f"Msg:{board_msg[:12]}", "L:Pull   R:Push")
    last_l = 1
    last_r = 1
    rand_seed = 0

    while True:
        vl = btn_left.value()
        vr = btn_right.value()
        rand_seed = (rand_seed + 1) % len(RANDOM_MESSAGES)

        # GP14 (Left): L:Pull 拉取試算表最新留言 (純讀取，不發送)
        if last_l == 1 and vl == 0:
            lcd_p("Pulling Cloud...", "Reading Text...")
            res, code = safe_gas_request(params="action=get_msg")
            if code == "OK":
                if isinstance(res, dict):
                    board_msg = str(res.get("message") or res.get("msg") or "No Msg")
                else:
                    board_msg = str(res)
                
                lcd_p("Sheet Message:", board_msg[:16])
                time.sleep(1.5)
                
                # 若文字超過 16 字元，啟動跑馬燈平滑捲動展示
                if len(board_msg) > 16:
                    scroll_str = "   " + board_msg + "   "
                    for idx in range(len(scroll_str) - 15):
                        if btn_left.value() == 0 or btn_right.value() == 0:
                            break
                        lcd.move_to(0, 1)
                        lcd.putstr(scroll_str[idx:idx+16])
                        time.sleep_ms(220)
            else:
                lcd_p("Pull Failed!", code[:16])
                time.sleep(1.5)

            lcd_p(f"Msg:{board_msg[:12]}", "L:Pull   R:Push")

        # GP16 (Right): R:Push 隨機挑選一句英文發布到試算表
        if last_r == 1 and vr == 0:
            # 隨機挑選一句英文 (利用時間戳記與迴圈計數做種子)
            chosen_msg = RANDOM_MESSAGES[(time.ticks_ms() + rand_seed) % len(RANDOM_MESSAGES)]
            
            lcd_p("Push Random Msg:", chosen_msg[:16])
            payload = {
                "action": "post_message",
                "device": "Pico2W",
                "message": chosen_msg,
                "ts": time.time()
            }
            res, code = safe_gas_request(payload=payload)
            if code == "OK":
                board_msg = chosen_msg
                lcd_p("Push Success!", chosen_msg[:16])
            else:
                lcd_p("Push Failed!", code[:16])
            time.sleep(1.8)
            lcd_p(f"Msg:{board_msg[:12]}", "L:Pull   R:Push")

        last_l = vl
        last_r = vr
        time.sleep_ms(20)

# ================= 8. 系統 4: AI 農業智慧灌溉決策系統 (Gemini 2.5 Flash 推理) =================
def run_sys_ai_agri():
    lcd_p("[AI Agriculture]", "R:Run Inference")
    last_l = 1
    last_r = 1

    def parse_gemini_json(raw_text):
        """安全提取 JSON 字典"""
        if not raw_text:
            return None
        text = raw_text.strip()
        # 去除 markdown 標籤
        if "```" in text:
            parts = text.split("```")
            for p in parts:
                p_clean = p.strip()
                if p_clean.startswith("json"):
                    p_clean = p_clean[4:].strip()
                if p_clean.startswith("{") and p_clean.endswith("}"):
                    text = p_clean
                    break
        try:
            # 尋找頭尾括號
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(text[start:end+1])
        except Exception:
            pass
        return None

    def execute_inference():
        # 步驟 1: 檢查與獲取試算表中的農田感測數據
        lcd_p("Reading Sheet...", "Checking Data...")
        res, code = safe_gas_request(params="action=get_farm_data")

        if code != "OK" or not isinstance(res, dict) or res.get("status") != "success":
            lcd_p("AI Agri", "No_data")
            time.sleep(2.0)
            lcd_p("[AI Agriculture]", "R:Run Inference")
            return

        # 取得農田五大要素
        humidity = res.get("humidity", 0)
        temp = res.get("temp", 0)
        soil_dry = res.get("soil_dryness", 0)
        soil_ec = res.get("soil_ec", 0)
        rain_fc = res.get("rain_forecast", "Unknown")

        # 步驟 2: 組織 Prompt 給 Gemini 2.5 Flash
        lcd_p("Farm Data OK!", "AI Thinking...")
        prompt = (
            f"You are an agricultural irrigation expert. Given farmland metrics: "
            f"Humidity: {humidity}%, Temp: {temp}C, Soil Dryness: {soil_dry}%, "
            f"Soil EC: {soil_ec}, Rain Forecast: {rain_fc}. "
            f"Decide whether to water or not. "
            f"Reply ONLY in valid JSON format with keys: "
            f"'water' (boolean), 'decision' (string: 'WATER' or 'NO WATER'), "
            f"'reason' (string, maximum 16 characters in English for 1602 LCD). "
            f"No explanation outside JSON."
        )

        gemini_out, gemini_code = call_gemini_flash(prompt)
        decision = "UNKNOWN"
        reason = "AI Timeout"

        if gemini_code == "OK" and gemini_out:
            parsed = parse_gemini_json(gemini_out)
            if parsed:
                decision = "WATER" if parsed.get("water") is True or parsed.get("decision") == "WATER" else "NO WATER"
                reason = str(parsed.get("reason", "OK"))[:16]
            else:
                # Fallback 依據土壤乾度預設決策
                decision = "WATER" if soil_dry >= 70 else "NO WATER"
                reason = "Dry: " + str(soil_dry) + "%"
        else:
            lcd_p("AI Inference Err", gemini_code[:16])
            time.sleep(1.8)
            # 若 AI 離線，依規則 Fallback
            decision = "WATER" if soil_dry >= 70 else "NO WATER"
            reason = "Offline Rule"

        # 步驟 3: LCD1602 螢幕呈現決策結果
        lcd.clear()
        line0 = f">> {decision} <<"[:16].center(16)
        line1 = reason[:16]
        lcd_p(line0, line1)
        time.sleep(3.0)

        # 步驟 4: 在試算表上留下日誌 (FarmLogs)
        lcd_p("Logging Cloud...", "Saving Record..")
        payload = {
            "action": "log_ai_decision",
            "device": "Pico2W",
            "decision": decision,
            "reason": reason,
            "humidity": humidity,
            "temp": temp,
            "soil_dryness": soil_dry,
            "soil_ec": soil_ec,
            "rain_forecast": rain_fc,
            "ts": time.time()
        }
        log_res, log_code = safe_gas_request(payload=payload)
        if log_code == "OK":
            lcd_p("Log Inscribed!", decision[:16])
        else:
            lcd_p("Log Offline", decision[:16])
        time.sleep(1.8)

        lcd_p("[AI Agriculture]", "R:Run Inference")

    while True:
        vl = btn_left.value()
        vr = btn_right.value()

        # 右鍵 (GP16): 執行 AI 推理流程
        if last_r == 1 and vr == 0:
            execute_inference()
            time.sleep_ms(200)

        # 左鍵 (GP14): 提示操作
        if last_l == 1 and vl == 0:
            lcd_p("Press R to Run", "AI Inference")
            time.sleep(1.2)
            lcd_p("[AI Agriculture]", "R:Run Inference")
            time.sleep_ms(200)

        last_l = vl
        last_r = vr
        time.sleep_ms(20)

# ================= 主流程 =================
def main():
    play_ceremony()
    auto_wifi()
    while True:
        choice = main_menu()
        if choice == 0:
            run_sys_fortune()
        elif choice == 1:
            run_sys_msg()
        elif choice == 2:
            run_sys_sync()
        elif choice == 3:
            run_sys_ai_agri()

if __name__ == "__main__":
    main()
