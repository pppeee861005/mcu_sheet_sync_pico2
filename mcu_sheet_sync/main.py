# -*- coding: utf-8 -*-
"""
SkyDeck OS v1.0 (極客掌上微系統)
具備高儀式感開機動畫、開機雙 Wi-Fi 選單，以及雙系統切換架構：
  - 系統 1: SkySync (天氣與雲端試算表鏡像儀)
  - 系統 2: CloudMsg (桌上型雲端悄悄話與留言看板)

硬體配置：
  - 主控：ESP32-S3 DevKitC-1
  - 螢幕：0.96" OLED (SSD1306, SDA=21, SCL=22)
  - 操控：左鍵 (GPIO 18 - Next) / 右鍵 (GPIO 4 - Enter / Confirm)
"""

import time
import network
import urequests
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C

# ================= 雲端 API 設定 =================
GAS_URL = "https://script.google.com/macros/s/AKfycbxoD1kKYdviVGMdkKKrEJbMcynRfzQEnFfguewhckH4DtQ4SiHoOVoot-wicooF000u/exec"

# ================= Wi-Fi 熱點設定 =================
WIFI_CONFIGS = [
    {"ssid": "Redmi 13C", "pass": "chdmchkcrdfd7e8"},  # 手機熱點
    {"ssid": "egg5630", "pass": "27985630"}           # 家用 Wi-Fi
]

# ================= 硬體腳位定義 =================
I2C_SDA_PIN = 21
I2C_SCL_PIN = 22
BUTTON_LEFT_PIN = 18   # 左鍵
BUTTON_RIGHT_PIN = 4   # 右鍵

OLED_WIDTH = 128
OLED_HEIGHT = 64

# ================= 硬體初始化 =================
i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=400000)
oled = SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c)

btn_left = Pin(BUTTON_LEFT_PIN, Pin.IN, Pin.PULL_UP)
btn_right = Pin(BUTTON_RIGHT_PIN, Pin.IN, Pin.PULL_UP)

current_ip = "Offline"

# ================= 1. 極高儀式感開機動畫 =================
def play_ceremony_welcome():
    """科幻感滿載的極客開機儀式：星空匯聚、進度條解鎖、標題呼吸進場"""
    oled.fill(0)
    oled.show()
    
    # 階段 1：掃描線與星芒微光
    for r in range(4):
        oled.fill(0)
        # 繪製中央十字能量準星
        oled.hline(64 - r*10, 32, r*20, 1)
        oled.vline(64, 32 - r*6, r*12, 1)
        oled.show()
        time.sleep_ms(60)
        
    # 階段 2：外框幾何展開
    for w in range(20, 126, 18):
        oled.fill(0)
        h = int(w * 0.45)
        x = (128 - w) // 2
        y = (64 - h) // 2
        oled.rect(x, y, w, h, 1)
        oled.text("INITIALIZING", 16, 28, 1)
        oled.show()
        time.sleep_ms(40)
        
    # 階段 3：進度光條加載
    for step in range(0, 101, 20):
        oled.fill(0)
        oled.rect(14, 40, 100, 8, 1)
        oled.fill_rect(16, 42, int(step * 0.96), 4, 1)
        oled.text(">> SKYDECK OS <<", 4, 14, 1)
        oled.text(f"BOOTING {step}%", 24, 52, 1)
        oled.show()
        time.sleep_ms(80)
        
    # 階段 4：WELCOME 閃爍震撼登場
    oled.fill(0)
    oled.fill_rect(0, 0, 128, 64, 1) # 全屏白閃
    oled.show()
    time.sleep_ms(50)
    
    oled.fill(0)
    oled.fill_rect(0, 4, 128, 14, 1)
    oled.text("* SKYDECK OS *", 10, 7, 0)
    oled.text("=================", 0, 24, 1)
    oled.text("  WELCOME, MAKER!", 0, 36, 1)
    oled.text("=================", 0, 48, 1)
    oled.show()
    time.sleep(1.8)

# ================= 2. 開機 Wi-Fi 二選一選單 =================
def select_and_connect_wifi():
    global current_ip
    wifi_list = [
        {"name": "1. Redmi 13C (Phone)", "cfg": WIFI_CONFIGS[0]},
        {"name": "2. egg5630   (Home)",  "cfg": WIFI_CONFIGS[1]}
    ]
    selected_idx = 0
    timeout_seconds = 5
    start_tick = time.time()
    last_sec_displayed = -1
    
    def render_menu(idx, sec_left):
        oled.fill(0)
        oled.fill_rect(0, 0, 128, 13, 1)
        oled.text(f"Wi-Fi Setup ({sec_left}s)", 4, 3, 0)
        
        prefix1 = "> " if idx == 0 else "  "
        oled.text(prefix1 + "Redmi 13C (Phone)", 0, 20, 1)
        prefix2 = "> " if idx == 1 else "  "
        oled.text(prefix2 + "egg5630   (Home)", 0, 34, 1)
        
        oled.hline(0, 48, 128, 1)
        oled.text("L:Next  R:Connect", 0, 52, 1)
        oled.show()
        
    render_menu(selected_idx, timeout_seconds)
    last_l = 1
    last_r = 1
    
    while True:
        elapsed = time.time() - start_tick
        sec_left = max(0, timeout_seconds - elapsed)
        
        if sec_left != last_sec_displayed:
            last_sec_displayed = sec_left
            render_menu(selected_idx, sec_left)
            
        if elapsed >= timeout_seconds:
            target_cfg = wifi_list[selected_idx]["cfg"]
            break
            
        vl = btn_left.value()
        vr = btn_right.value()
        
        if last_l == 1 and vl == 0:
            time.sleep_ms(30)
            if btn_left.value() == 0:
                selected_idx = (selected_idx + 1) % len(wifi_list)
                start_tick = time.time()
                render_menu(selected_idx, timeout_seconds)
                while btn_left.value() == 0:
                    time.sleep_ms(20)
                    
        if last_r == 1 and vr == 0:
            time.sleep_ms(30)
            if btn_right.value() == 0:
                target_cfg = wifi_list[selected_idx]["cfg"]
                while btn_right.value() == 0:
                    time.sleep_ms(20)
                break
                
        last_l = vl
        last_r = vr
        time.sleep_ms(20)
        
    # 連線 Wi-Fi
    wlan = network.WLAN(network.STA_IF)
    if not wlan.active():
        wlan.active(True)
    time.sleep_ms(200)
    
    ssid = target_cfg["ssid"]
    pwd = target_cfg["pass"]
    try:
        wlan.disconnect()
        time.sleep_ms(200)
    except:
        pass
    wlan.connect(ssid, pwd)
    
    t0 = time.time()
    dot = 0
    while not wlan.isconnected() and time.time() - t0 < 15:
        dot = (dot % 3) + 1
        oled.fill(0)
        oled.fill_rect(0, 0, 128, 12, 1)
        oled.text("[ SkyDeck IoT ]", 4, 2, 0)
        oled.text("Connecting Wi-Fi:", 0, 20, 1)
        oled.text(ssid[:15], 0, 34, 1)
        oled.text("Please wait" + "." * dot, 0, 48, 1)
        oled.show()
        time.sleep_ms(400)
        
    if wlan.isconnected():
        current_ip = wlan.ifconfig()[0]
        oled.fill(0)
        oled.fill_rect(0, 0, 128, 12, 1)
        oled.text("Wi-Fi Connected!", 2, 2, 0)
        oled.text(f"SSID: {ssid}", 0, 24, 1)
        oled.text(f"IP: {current_ip}", 0, 40, 1)
        oled.show()
        time.sleep(1.2)
        return True
    else:
        oled.fill(0)
        oled.text("Wi-Fi Failed!", 10, 24, 1)
        oled.text("Running Offline", 5, 40, 1)
        oled.show()
        time.sleep(1.2)
        return False

# ================= 3. 多系統選擇選單 (System Selector) =================
SYSTEMS = [
    {"id": "SKY_SYNC", "title": "1. SkySync Weather", "desc": "Weather Sync App"},
    {"id": "CLOUD_MSG", "title": "2. Cloud Msg Board", "desc": "Live Sheet Notes"},
    {"id": "POMODORO", "title": "3. Pomodoro Tracker", "desc": "Focus & Sheet Log"}
]

def select_system():
    idx = 0
    def render_sys_menu(selected):
        oled.fill(0)
        oled.fill_rect(0, 0, 128, 13, 1)
        oled.text("[ SELECT SYSTEM ]", 2, 3, 0)
        
        oled.text(f"> {SYSTEMS[selected]['title']}", 0, 20, 1)
        oled.text(f"  {SYSTEMS[selected]['desc']}", 0, 34, 1)
        
        oled.hline(0, 48, 128, 1)
        oled.text("L:Next    R:Enter", 0, 52, 1)
        oled.show()
        
    render_sys_menu(idx)
    last_l = 1
    last_r = 1
    
    while True:
        vl = btn_left.value()
        vr = btn_right.value()
        
        if last_l == 1 and vl == 0:
            time.sleep_ms(30)
            if btn_left.value() == 0:
                idx = (idx + 1) % len(SYSTEMS)
                render_sys_menu(idx)
                while btn_left.value() == 0:
                    time.sleep_ms(20)
                    
        if last_r == 1 and vr == 0:
            time.sleep_ms(30)
            if btn_right.value() == 0:
                while btn_right.value() == 0:
                    time.sleep_ms(20)
                return SYSTEMS[idx]["id"]
                
        last_l = vl
        last_r = vr
        time.sleep_ms(20)

# ================= 4. 系統 1：SkySync (天氣監控系統) =================
WEATHER_STATES = [
    {"id": "SUNNY", "title": "[ SUNNY / Sunny ]", "icon_type": "sun", "desc": "Weather is clear", "alert": "Condition: Normal", "message": "Sunny_Clear"},
    {"id": "RAIN", "title": "[ HEAVY RAIN ]", "icon_type": "rain", "desc": "Rain: > 50 mm/hr", "alert": "Drive with care!", "message": "Heavy_Rain_Warning"},
    {"id": "FLOOD", "title": "[ FLOOD ALERT! ]", "icon_type": "flood", "desc": "Water level: HIGH", "alert": "** DANGER WARNING **", "message": "Flood_Alert_Danger"}
]

def draw_icon(icon_type):
    cx, cy = 110, 30
    if icon_type == "sun":
        oled.fill_rect(cx - 5, cy - 5, 11, 11, 1)
        oled.line(cx, cy - 9, cx, cy - 6, 1)
        oled.line(cx, cy + 6, cx, cy + 9, 1)
        oled.line(cx - 9, cy, cx - 6, cy, 1)
        oled.line(cx + 6, cy, cx + 9, cy, 1)
        oled.line(cx - 7, cy - 7, cx - 5, cy - 5, 1)
        oled.line(cx + 5, cy + 5, cx + 7, cy + 7, 1)
        oled.line(cx - 7, cy + 7, cx - 5, cy + 5, 1)
        oled.line(cx + 5, cy - 5, cx + 7, cy - 7, 1)
    elif icon_type == "rain":
        oled.fill_rect(cx - 10, cy - 8, 20, 8, 1)
        oled.fill_rect(cx - 6, cy - 12, 12, 5, 1)
        oled.line(cx - 8, cy + 3, cx - 11, cy + 9, 1)
        oled.line(cx - 2, cy + 3, cx - 5, cy + 9, 1)
        oled.line(cx + 4, cy + 3, cx + 1, cy + 9, 1)
        oled.line(cx + 9, cy + 3, cx + 6, cy + 9, 1)
    elif icon_type == "flood":
        oled.line(cx, cy - 12, cx - 10, cy + 3, 1)
        oled.line(cx, cy - 12, cx + 10, cy + 3, 1)
        oled.line(cx - 10, cy + 3, cx + 10, cy + 3, 1)
        oled.line(cx, cy - 7, cx, cy - 2, 1)
        oled.pixel(cx, cy + 1, 1)
        oled.line(cx - 12, cy + 8, cx - 6, cy + 6, 1)
        oled.line(cx - 6, cy + 6, cx, cy + 8, 1)
        oled.line(cx, cy + 8, cx + 6, cy + 6, 1)
        oled.line(cx + 6, cy + 6, cx + 12, cy + 8, 1)

def run_skysync():
    cur_idx = 0
    cnt = 0
    is_dirty = False
    
    def render_weather(status_msg=None):
        st = WEATHER_STATES[cur_idx]
        oled.fill(0)
        oled.fill_rect(0, 0, 128, 13, 1)
        oled.text(st["title"], 2, 3, 0)
        oled.text(st["desc"], 0, 18, 1)
        oled.text(st["alert"], 0, 32, 1)
        draw_icon(st["icon_type"])
        oled.hline(0, 48, 128, 1)
        if status_msg:
            oled.text(status_msg, 0, 52, 1)
        else:
            oled.text("L:Next  R:[OK!]" if is_dirty else "L:Next  R:Send", 0, 52, 1)
        oled.show()
        
    render_weather()
    last_l = 1
    last_r = 1
    
    while True:
        vl = btn_left.value()
        vr = btn_right.value()
        
        # 左鍵切換天氣
        if last_l == 1 and vl == 0:
            time.sleep_ms(30)
            if btn_left.value() == 0:
                cur_idx = (cur_idx + 1) % len(WEATHER_STATES)
                is_dirty = True
                render_weather()
                t_rel = time.time()
                while btn_left.value() == 0 and time.time() - t_rel < 1:
                    time.sleep_ms(20)
                    
        # 右鍵確認送出
        if last_r == 1 and vr == 0:
            time.sleep_ms(30)
            if btn_right.value() == 0:
                cnt += 1
                st = WEATHER_STATES[cur_idx]
                render_weather("Syncing Sheet...")
                try:
                    wlan = network.WLAN(network.STA_IF)
                    if wlan.isconnected():
                        url = f"{GAS_URL}?device=SkySync_ESP32&event=Weather_{st['id']}&count={cnt}&msg={st['message']}"
                        r = urequests.get(url)
                        r.close()
                        render_weather("Sheet Synced! OK")
                    else:
                        render_weather("Offline Mode")
                except:
                    render_weather("Upload Error!")
                time.sleep(1.2)
                is_dirty = False
                render_weather()
                t_rel = time.time()
                while btn_right.value() == 0 and time.time() - t_rel < 1:
                    time.sleep_ms(20)
                    
        last_l = vl
        last_r = vr
        time.sleep_ms(20)

# ================= 5. 系統 2：Cloud Msg Board (雲端悄悄話看板) =================
def run_cloud_msg():
    current_note = "Fetching Cloud..."
    sender_name = "Cloud"
    last_fetch = 0
    reply_count = 0
    
    def fetch_latest():
        nonlocal current_note, sender_name
        try:
            wlan = network.WLAN(network.STA_IF)
            if not wlan.isconnected():
                current_note = "Offline"
                return
            r = urequests.get(f"{GAS_URL}?action=get_msg")
            if r.status_code == 200:
                data = r.json()
                if data.get("status") == "success":
                    current_note = data.get("message", "No Message")
                    sender_name = data.get("sender", "Cloud")
            r.close()
        except Exception as e:
            current_note = "Connect Error"

    def render_board(hint=None):
        oled.fill(0)
        oled.fill_rect(0, 0, 128, 13, 1)
        oled.text(f"MSG: {sender_name[:10]}", 2, 3, 0)
        
        # 顯示留言本文
        oled.text(">> Message <<", 0, 18, 1)
        oled.text(current_note[:16], 0, 32, 1)
        
        oled.hline(0, 48, 128, 1)
        if hint:
            oled.text(hint, 0, 52, 1)
        else:
            oled.text("L:Pull  R:ReplyOK", 0, 52, 1)
        oled.show()

    fetch_latest()
    render_board()
    last_l = 1
    last_r = 1
    last_auto_fetch = time.time()
    
    while True:
        # 每 20 秒自動幫你刷新一次試算表留言
        if time.time() - last_auto_fetch > 20:
            fetch_latest()
            render_board()
            last_auto_fetch = time.time()
            
        vl = btn_left.value()
        vr = btn_right.value()
        
        # 左鍵手動刷新留言 (Pull)
        if last_l == 1 and vl == 0:
            time.sleep_ms(30)
            if btn_left.value() == 0:
                render_board("Refreshing...")
                fetch_latest()
                last_auto_fetch = time.time()
                render_board("Updated!")
                time.sleep(1)
                render_board()
                t_rel = time.time()
                while btn_left.value() == 0 and time.time() - t_rel < 1:
                    time.sleep_ms(20)
                    
        # 右鍵回傳已收到 (Reply)
        if last_r == 1 and vr == 0:
            time.sleep_ms(30)
            if btn_right.value() == 0:
                reply_count += 1
                render_board("Sending Reply...")
                
                # 釋放按鍵並加入超時防卡死保護
                t_rel = time.time()
                while btn_right.value() == 0 and time.time() - t_rel < 1:
                    time.sleep_ms(20)
                    
                try:
                    wlan = network.WLAN(network.STA_IF)
                    if wlan.isconnected():
                        url = f"{GAS_URL}?device=SkyDeck_ESP32&event=Msg_Ack&count={reply_count}&msg=Roger_That_Received"
                        r = urequests.get(url)
                        r.close()
                        render_board("Reply Sent! OK")
                    else:
                        render_board("Offline")
                except Exception as e:
                    print("Reply error:", e)
                    render_board("Send Failed!")
                    
                time.sleep(1.2)
                render_board()
                    
        last_l = vl
        last_r = vr
        time.sleep_ms(20)


# ================= 6. 系統 3：Pomodoro Tracker (番茄鐘專注打卡機) =================
POMO_MODES = [
    {"name": "25m Focus", "secs": 25 * 60, "label": "25min_Focus"},
    {"name": "5m Break",  "secs": 5 * 60,  "label": "5min_Break"},
    {"name": "10m Sprint", "secs": 10 * 60, "label": "10min_Sprint"},
    {"name": "10s Test",   "secs": 10,      "label": "10sec_Demo"}
]

def run_pomodoro():
    mode_idx = 0
    is_running = False
    time_left = POMO_MODES[mode_idx]["secs"]
    last_tick = time.time()
    completed_count = 0
    
    def render_pomo(status_text=None):
        oled.fill(0)
        oled.fill_rect(0, 0, 128, 13, 1)
        cur_m = POMO_MODES[mode_idx]
        oled.text(f"[ {cur_m['name']} ]", 2, 3, 0)
        
        if status_text:
            oled.text(status_text[:16], 0, 26, 1)
        else:
            mins = time_left // 60
            secs = time_left % 60
            time_str = f"{mins:02d}:{secs:02d}"
            oled.text(f">> {time_str} <<", 14, 20, 1)
            
            total_s = cur_m["secs"]
            progress = max(0.0, min(1.0, 1.0 - (time_left / total_s)))
            oled.rect(14, 34, 100, 7, 1)
            oled.fill_rect(16, 36, int(progress * 96), 3, 1)
            
        oled.hline(0, 48, 128, 1)
        if is_running:
            oled.text("R:Pause  L:Reset", 0, 52, 1)
        else:
            oled.text("L:Mode   R:Start", 0, 52, 1)
        oled.show()

    def sync_completion_to_sheet(mode_label):
        nonlocal completed_count
        completed_count += 1
        render_pomo("Syncing Sheet...")
        try:
            import gc
            gc.collect()
            wlan = network.WLAN(network.STA_IF)
            if wlan.isconnected():
                url = f"{GAS_URL}?device=Pomodoro_ESP32&event=Pomodoro_Done&count={completed_count}&msg={mode_label}"
                r = urequests.get(url)
                r.close()
                render_pomo("Sheet Synced! OK")
            else:
                render_pomo("Offline Done!")
        except Exception as e:
            print("Pomo upload err:", e)
            render_pomo("Upload Error!")
        time.sleep(1.5)

    render_pomo()
    last_l = 1
    last_r = 1
    
    while True:
        if is_running:
            now = time.time()
            if now != last_tick:
                elapsed = now - last_tick
                last_tick = now
                time_left = max(0, time_left - elapsed)
                render_pomo()
                
                if time_left == 0:
                    is_running = False
                    for _ in range(3):
                        oled.fill(0)
                        oled.fill_rect(0, 0, 128, 64, 1)
                        oled.show()
                        time.sleep_ms(80)
                        oled.fill(0)
                        oled.show()
                        time.sleep_ms(80)
                    
                    oled.fill(0)
                    oled.fill_rect(0, 0, 128, 13, 1)
                    oled.text("* SUCCESS! *", 18, 3, 0)
                    oled.text("POMODORO DONE!", 8, 26, 1)
                    oled.show()
                    time.sleep(1.2)
                    
                    cur_label = POMO_MODES[mode_idx]["label"]
                    sync_completion_to_sheet(cur_label)
                    
                    time_left = POMO_MODES[mode_idx]["secs"]
                    render_pomo()
                    
        vl = btn_left.value()
        vr = btn_right.value()
        
        if last_l == 1 and vl == 0:
            time.sleep_ms(30)
            if btn_left.value() == 0:
                if is_running:
                    is_running = False
                    time_left = POMO_MODES[mode_idx]["secs"]
                    render_pomo()
                else:
                    mode_idx = (mode_idx + 1) % len(POMO_MODES)
                    time_left = POMO_MODES[mode_idx]["secs"]
                    render_pomo()
                while btn_left.value() == 0:
                    time.sleep_ms(20)
                    
        if last_r == 1 and vr == 0:
            time.sleep_ms(30)
            if btn_right.value() == 0:
                is_running = not is_running
                last_tick = time.time()
                render_pomo()
                while btn_right.value() == 0:
                    time.sleep_ms(20)
                    
        last_l = vl
        last_r = vr
        time.sleep_ms(40)

# ================= 主程式進入點 =================
def main():
    print("=============================================")
    print("  SkyDeck OS v1.0 - Multi-System IoT Platform")
    print("=============================================")
    
    # 儀式 1：超酷炫開機動畫
    play_ceremony_welcome()
    
    # 儀式 2：雙 Wi-Fi 選單連線
    select_and_connect_wifi()
    
    # 儀式 3：多系統選擇
    selected_app = select_system()
    
    # 進入對應系統
    if selected_app == "SKY_SYNC":
        print(">> 啟動系統 1: SkySync 天氣鏡像儀")
        run_skysync()
    elif selected_app == "CLOUD_MSG":
        print(">> 啟動系統 2: Cloud Msg Board 雲端悄悄話看板")
        run_cloud_msg()
    elif selected_app == "POMODORO":
        print(">> 啟動系統 3: Pomodoro Tracker 番茄鐘專注打卡機")
        run_pomodoro()

if __name__ == "__main__":
    main()
