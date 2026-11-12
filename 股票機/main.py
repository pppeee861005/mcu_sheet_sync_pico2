# main.py - 股票機 (Pico 2 W 大盤指數監控機 - 神諭降臨 v1.01 儀式感版)
# 支援多 Wi-Fi 容錯、神壇 Landing Page、打字機動態咒語詠唱、GAS 輕量 API 串接、緩慢跑馬燈天機揭曉

import time
import network
import urequests
from machine import Pin, I2C
from pico_i2c_lcd import I2cLcd
from config import WIFI_NETWORKS, GAS_SCRIPT_ID

# -------------------------------------------------------------
# 硬體腳位定義 (遵循 mcu_sheet_sync_pico2 規範)
# -------------------------------------------------------------
I2C_SDA_PIN = 0   # GP0 (Pin 1)
I2C_SCL_PIN = 1   # GP1 (Pin 2)
BTN_PRAY    = 14  # GP14 (Pin 19) 開壇祈願 / 召喚天機
BTN_TOGGLE  = 16  # GP16 (Pin 21) 切換背光 (靜心/開關)

# -------------------------------------------------------------
# LCD1602 自訂神聖點陣圖標 (5x8 點陣)
# -------------------------------------------------------------
# 0 號字元：▲ 漲勢符文
ICON_UP = bytearray([
    0b00100,
    0b01110,
    0b11111,
    0b00100,
    0b00100,
    0b00100,
    0b00000,
    0b00000
])

# 1 號字元：▼ 跌勢符文
ICON_DOWN = bytearray([
    0b00100,
    0b00100,
    0b00100,
    0b11111,
    0b01110,
    0b00100,
    0b00000,
    0b00000
])

# 2 號字元：✦ 神聖星芒符文
ICON_STAR = bytearray([
    0b00100,
    0b00100,
    0b10101,
    0b01110,
    0b10101,
    0b00100,
    0b00100,
    0b00000
])

# 3 號字元：⟐ 神諭靈石符文
ICON_ORACLE = bytearray([
    0b00000,
    0b00100,
    0b01110,
    0b11011,
    0b11011,
    0b01110,
    0b00100,
    0b00000
])

# 4 號字元：⏳ 沙漏滿 / 上層沙 (Hourglass Full)
ICON_SAND_1 = bytearray([
    0b11111,
    0b11111,
    0b01110,
    0b00100,
    0b01010,
    0b10001,
    0b11111,
    0b00000
])

# 5 號字元：⌛ 沙漏半 / 漏沙中 (Hourglass Mid)
ICON_SAND_2 = bytearray([
    0b11111,
    0b10001,
    0b01110,
    0b00100,
    0b01110,
    0b10101,
    0b11111,
    0b00000
])

# 6 號字元：⌛ 沙漏空 / 下層沙滿 (Hourglass Low)
ICON_SAND_3 = bytearray([
    0b11111,
    0b10001,
    0b01010,
    0b00100,
    0b01110,
    0b11111,
    0b11111,
    0b00000
])

# -------------------------------------------------------------
# 模組初始化
# -------------------------------------------------------------
i2c = I2C(0, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=100000)
devices = i2c.scan()
if not devices:
    raise RuntimeError("未檢測到 I2C 設備，請檢查 LCD1602 接線 (GP0/GP1/VBUS)")

lcd_addr = devices[0]
lcd = I2cLcd(i2c, lcd_addr, 2, 16)
lcd.custom_char(0, ICON_UP)
lcd.custom_char(1, ICON_DOWN)
lcd.custom_char(2, ICON_STAR)
lcd.custom_char(3, ICON_ORACLE)
lcd.custom_char(4, ICON_SAND_1)
lcd.custom_char(5, ICON_SAND_2)
lcd.custom_char(6, ICON_SAND_3)

btn_pray   = Pin(BTN_PRAY,   Pin.IN, Pin.PULL_UP)
btn_toggle = Pin(BTN_TOGGLE, Pin.IN, Pin.PULL_UP)
backlight_on = True

# -------------------------------------------------------------
# 視覺特效子程式 (打字機、跑馬燈、神聖微閃)
# -------------------------------------------------------------
def lcd_show_message(line1, line2=""):
    """安全清屏並靜態顯示兩行訊息"""
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr(line1[:16])
    if line2:
        lcd.move_to(0, 1)
        lcd.putstr(line2[:16])

def typewriter_print(line, text, delay=0.07):
    """緩慢打字機特效，營造神秘符文浮現感"""
    lcd.move_to(0, line)
    # 先填滿 16 個空白清理該行
    lcd.putstr(" " * 16)
    lcd.move_to(0, line)
    for ch in text[:16]:
        lcd.putchar(ch)
        time.sleep(delay)

def holy_backlight_pulse():
    """神聖背光閃爍特效 (開壇/天門初開)"""
    for _ in range(2):
        lcd.backlight_off()
        time.sleep(0.08)
        lcd.backlight_on()
        time.sleep(0.12)

def hourglass_countdown_animation(seconds=3):
    """
    3秒神聖沙漏滴落與倒數動畫
    包含動態沙漏圖標 (4:滿 -> 5:滴沙中 -> 6:流盡) 與神聖進度點陣
    """
    icons = [4, 5, 6]  # 沙漏動態幀
    for sec in range(seconds, 0, -1):
        # 每一秒細分為兩幀動態流沙
        for sub_step, icon_idx in enumerate([icons[3 - sec], icons[min(4 - sec, 2)]]):
            lcd.clear()
            # 第一行：✦ TIME WEAVING ✦
            lcd.move_to(0, 0)
            lcd.putchar(chr(2))
            lcd.putstr(" TIME WEAVING ")
            lcd.putchar(chr(2))

            # 第二行：沙漏滴落圖標 + 倒數數字 + 動態滴漏點點
            # 格式例如："   [⌛] 3s ...   "
            dots = "." * (4 - sec) + ("." if sub_step == 1 else " ")
            line2 = f"   [{chr(icon_idx)}] {sec}s {dots:<4}   "
            lcd.move_to(0, 1)
            lcd.putstr(line2[:16])
            time.sleep(0.5)

    # 倒數結束瞬間清脆提示
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putchar(chr(2))
    lcd.putstr(" DESTINY CAST ")
    lcd.putchar(chr(2))
    lcd.move_to(0, 1)
    lcd.putstr("   [!] READY    ")
    time.sleep(0.6)

def marquee_display_dual(line1_text, line2_text, speed=0.45, loops=2):
    """
    雙行同步超慢速走馬燈展示天機 (速度放慢約 70%，每格 0.45 秒)
    line1_text: 第一行長字串 (含 TAIEX 指數與漲跌圖標)
    line2_text: 第二行長字串 (含吉凶神諭與詳細點數)
    speed: 每格滾動秒數 (0.45s，極具儀式與沉浸感)
    loops: 捲動循環次數，期間可按任意鍵提前跳過
    """
    pad1 = "    " + line1_text + "    "
    pad2 = "    " + line2_text + "    "
    max_len = max(len(pad1), len(pad2))
    
    # MicroPython 精簡語法相容 (無 ljust 內建方法)
    if len(pad1) < max_len:
        pad1 += " " * (max_len - len(pad1))
    if len(pad2) < max_len:
        pad2 += " " * (max_len - len(pad2))

    for _ in range(loops):
        for i in range(max_len - 15):
            # 支援隨時按鍵打斷提早返回
            if btn_pray.value() == 0 or btn_toggle.value() == 0:
                time.sleep(0.3)
                return

            lcd.move_to(0, 0)
            lcd.putstr(pad1[i:i + 16])
            lcd.move_to(0, 1)
            lcd.putstr(pad2[i:i + 16])
            time.sleep(speed)

# -------------------------------------------------------------
# 網路連線管理 (優先手機熱點，家用備援)
# -------------------------------------------------------------
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        return True

    for net in WIFI_NETWORKS:
        ssid = net.get("ssid", "")
        pwd = net.get("password", "")
        lcd_show_message("Awakening Link", ssid[:16])
        print(f"[WiFi] 嘗試連線至: {ssid}...")
        wlan.connect(ssid, pwd)

        start_time = time.time()
        while not wlan.isconnected():
            if time.time() - start_time > 10:
                print(f"[WiFi] 連線 {ssid} 逾時，嘗試下一組...")
                break
            time.sleep(0.5)

        if wlan.isconnected():
            ip = wlan.ifconfig()[0]
            print(f"[WiFi] 連線成功! IP: {ip}")
            lcd_show_message("Portal Opened!", ip[:16])
            time.sleep(1.2)
            return True

    lcd_show_message("Portal Failed!", "Check config.py")
    return False

# -------------------------------------------------------------
# GAS API 行情抓取
# -------------------------------------------------------------
def fetch_stock_data():
    """向 Google Apps Script 獲取最新大盤資料"""
    url = f"https://script.google.com/macros/s/{GAS_SCRIPT_ID}/exec"
    print(f"[HTTP] 恭請天機 (請求 GAS API): {url}...")
    try:
        res = urequests.get(url)
        if res.status_code == 200:
            data = res.json()
            res.close()
            return data
        else:
            print(f"[HTTP] 天機未至，狀態碼異常: {res.status_code}")
            res.close()
            return None
    except Exception as e:
        print(f"[HTTP] 連繫虛空異常: {e}")
        return None

# -------------------------------------------------------------
# 儀式流程：Landing Page & 召喚神諭
# -------------------------------------------------------------
CACHED_DATA = None  # 全域快取：整個運行過程僅抓取一次天機

def render_landing_page():
    """顯示靜態神壇 Landing Page"""
    lcd.clear()
    # 第一行：✦ GEEK  ORACLE ✦
    lcd.move_to(0, 0)
    lcd.putchar(chr(2))
    lcd.putstr(" GEEK  ORACLE ")
    lcd.putchar(chr(2))

    # 第二行：⟐ [Press to Pray]
    lcd.move_to(0, 1)
    lcd.putchar(chr(3))
    lcd.putstr(" [Press To Pray]")

def perform_incantation_ritual():
    """
    動態神諭召喚儀式：
    1. 打字機詠唱咒文
    2. 神聖背光閃爍
    3. 獲取天機 (優先使用快取，整個運行僅抓取一次 GAS API)
    4. 緩慢走馬燈揭曉指數
    """
    global CACHED_DATA
    print("[Ritual] 開壇起乩：信徒祈願天機...")
    lcd.clear()

    # 第一幕咒語：打字機逐字湧現
    typewriter_print(0, "Summoning Bull..", delay=0.06)
    time.sleep(0.4)
    typewriter_print(1, "Aligning Cosmos.", delay=0.06)
    time.sleep(0.5)

    # 第二幕神聖開光閃爍
    holy_backlight_pulse()

    # 第三幕宣告
    lcd.clear()
    typewriter_print(0, "Portal Open...", delay=0.05)
    typewriter_print(1, "Seeking Oracle..", delay=0.05)

    # 獲取天機：只抓取一次，後續祈願直接使用神諭快取
    if CACHED_DATA is None:
        print("[HTTP] 首次降靈，向雲端發送請求...")
        data = fetch_stock_data()
        if data and data.get("status") == "success":
            CACHED_DATA = data
    else:
        print("[Cache] 已參透今日天機，直接調用神諭快取！")
        time.sleep(0.3)

    data = CACHED_DATA

    if not data or data.get("status") != "success":
        lcd.clear()
        typewriter_print(0, "Oracle Silent..", delay=0.05)
        typewriter_print(1, "Cloud Untouched", delay=0.05)
        time.sleep(2)
        return

    # 第四幕：3 秒神聖沙漏滴落倒數動畫 (Hourglass Countdown)
    hourglass_countdown_animation(seconds=3)

    # 解析天機數據
    raw_idx = data.get("index", "0.00").replace(",", "")
    change = data.get("change", "0.00")
    direction = data.get("direction", "FLAT")

    # 判定符號與吉凶判詞
    if direction == "UP":
        dir_symbol = chr(0)  # ▲
        sentiment = "DIVINE BLESSING"
    elif direction == "DOWN":
        dir_symbol = chr(1)  # ▼
        sentiment = "BEARISH TRIAL"
    else:
        dir_symbol = "="
        sentiment = "SERENE WATERS"

    # 第一行長走馬燈文案：TAIEX 指數全展開 + 神聖符文
    marquee_line1 = f"{chr(2)} TAIEX INDEX: {raw_idx} {dir_symbol} {chr(2)}"

    # 第二行長走馬燈文案：吉凶判詞 + 詳細點數 + 祝福
    marquee_line2 = (
        f"{sentiment} | CHG: {change} "
        f"* MAY THE GAINS BE WITH YOU * {chr(3)}"
    )

    print(f"[Ritual] 天機揭曉:")
    print(f"  Line1: {marquee_line1}")
    print(f"  Line2: {marquee_line2}")

    # 執行慢 70% 的超慢速雙行跑馬燈展現天機 (speed=0.45s，跑 2 輪)
    marquee_display_dual(marquee_line1, marquee_line2, speed=0.45, loops=2)

    # 跑馬燈結束後，靜態停駐展示精簡結果 4 秒
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr(f"TAIEX:{raw_idx[:7]} {dir_symbol}"[:16])
    lcd.move_to(0, 1)
    lcd.putstr(f"CHG:{change:<7} {dir_symbol}"[:16])
    time.sleep(4)

# -------------------------------------------------------------
# 主程式
# -------------------------------------------------------------
def main():
    global backlight_on
    lcd_show_message("Sacred Oracle", "Initializing...")
    time.sleep(1)

    # 啟動連線
    if not connect_wifi():
        time.sleep(3)

    # 進入神殿靜態 Landing Page 待命
    render_landing_page()

    while True:
        # GP14: 開壇祈願 / 召喚天機 (Pray Button)
        if btn_pray.value() == 0:
            time.sleep(0.05)  # 按鍵防彈跳
            if btn_pray.value() == 0:
                perform_incantation_ritual()
                # 儀式完成後返回靜態神壇
                render_landing_page()

        # GP16: 切換背光 (靜心/開關)
        if btn_toggle.value() == 0:
            time.sleep(0.05)
            if btn_toggle.value() == 0:
                backlight_on = not backlight_on
                if backlight_on:
                    lcd.backlight_on()
                else:
                    lcd.backlight_off()
                print(f"[Hardware] 背光切換: {'開' if backlight_on else '關'}")
                time.sleep(0.3)

        time.sleep(0.05)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n儀式終止，神壇隱入虛空。")
        lcd.clear()
        lcd.putstr("Sacred Halted.")
