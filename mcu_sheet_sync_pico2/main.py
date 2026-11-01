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
from config import WIFI_NETWORKS, GAS_SCRIPT_ID

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
    {"name": "1.Sheet Sync", "desc": "Push Counter"},
    {"name": "2.CloudMsg",   "desc": "Pull Only (Read)"}
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

# ================= 6. 系統 1: Sheet Sync (上報同步) =================
def run_sys_sync():
    count = 0
    lcd_p("[1] Sheet Sync", f"L:+1  R:Push [{count}]")
    last_l = 1
    last_r = 1

    while True:
        vl = btn_left.value()
        vr = btn_right.value()

        # 雙鍵同按 -> 回主選單
        if vl == 0 and vr == 0:
            lcd_p("Exiting System..", "Back to Menu")
            time.sleep_ms(600)
            break

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

        # 雙鍵同按 -> 回主選單
        if vl == 0 and vr == 0:
            lcd_p("Exiting System..", "Back to Menu")
            time.sleep_ms(600)
            break

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

# ================= 主流程 =================
def main():
    play_ceremony()
    auto_wifi()
    while True:
        choice = main_menu()
        if choice == 0:
            run_sys_sync()
        elif choice == 1:
            run_sys_msg()

if __name__ == "__main__":
    main()
