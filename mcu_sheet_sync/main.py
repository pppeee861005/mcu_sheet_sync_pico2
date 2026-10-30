"""
MCU 與 Google 試算表同步主程式 (main.py)
硬體架構：ESP32-S3 + SSD1306 OLED (128x64) + 實體按鍵 (GPIO 18)
行為：
  1. 開機自動依序嘗試 Wi-Fi (家用 egg5630 -> 手機 Redmi 13C)
  2. 連線完成進入「待機中」
  3. 按下按鍵後，發送 HTTP POST 至 Google Apps Script (GAS) 寫入 Google 試算表
  4. OLED 顯示寫入結果後自動重返「待機中」
"""

from machine import Pin, I2C
import time
import network
import ujson
import urequests
import ssd1306

# ----------------- 硬體腳位配置 -----------------
SDA_PIN = 21
SCL_PIN = 22
BUTTON_PIN = 18

WIDTH = 128
HEIGHT = 64

# ----------------- Wi-Fi 候選清單 (依序嘗試) -----------------
WIFI_LIST = [
    ("egg5630", "27985630"),          # 優先：家用 Wi-Fi
    ("Redmi 13C", "chdmchkcrdfd7e8")  # 備援：手機熱點
]

# ----------------- Google Apps Script Web App URL -----------------
# 請換成您在 Google Apps Script 部署後生成的 Web App 網址
GAS_URL = "https://script.google.com/macros/s/AKfycbxYOUR_DEPLOYMENT_ID/exec"

# ----------------- 硬體初始化 -----------------
i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=400000)
oled = ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c)
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

# 全域計數器
press_count = 0


def display_msg(line1="", line2="", line3="", line4=""):
    """在 OLED 畫面上顯示最多 4 行文字"""
    oled.fill(0)
    if line1:
        oled.text(line1, 0, 0)
    if line2:
        oled.text(line2, 0, 16)
    if line3:
        oled.text(line3, 0, 32)
    if line4:
        oled.text(line4, 0, 48)
    oled.show()


def auto_connect_wifi():
    """自動輪詢嘗試候選 Wi-Fi 清單"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    for ssid, pwd in WIFI_LIST:
        print(f"嘗試連線 Wi-Fi: {ssid} ...")
        display_msg("WiFi Connecting:", ssid, "Please wait...")
        
        wlan.disconnect()
        time.sleep(0.5)
        wlan.connect(ssid, pwd)

        # 等待最多 8 秒 (16 * 0.5s)
        for _ in range(16):
            if wlan.isconnected():
                ip = wlan.ifconfig()[0]
                print(f"✅ 成功連上: {ssid} (IP: {ip})")
                display_msg("WiFi Connected!", ssid, f"IP:{ip}")
                time.sleep(1.5)
                return True
            time.sleep(0.5)

        print(f"❌ {ssid} 連線逾時，切換下一組...")

    display_msg("WiFi Error!", "All failed.", "Check AP / pwd.")
    return False


def send_data_to_sheet(count):
    """送出資料至 Google Sheet"""
    payload = {
        "device": "ESP32-S3",
        "event": "Button_Press",
        "press_count": count,
        "message": "手動按鍵觸發寫入"
    }
    headers = {"Content-Type": "application/json"}

    print(f"發送數據至 Sheet: {payload}")
    display_msg("Sending Data...", f"Count: #{count}", "Uploading to", "Google Sheet...")

    try:
        # 注意：MicroPython 的 urequests 處理 302 重導向
        res = urequests.post(GAS_URL, data=ujson.dumps(payload), headers=headers)
        print("回應碼:", res.status_code)
        print("回應內容:", res.text)
        res.close()

        # 成功畫面
        display_msg("Upload Success!", f"Count: #{count}", "Sheet Updated", "OK!")
        time.sleep(2)
        return True
    except Exception as e:
        print("發送失敗:", e)
        display_msg("Upload Failed!", "Error:", str(e)[:16])
        time.sleep(2)
        return False


def show_standby():
    """顯示待機畫面"""
    display_msg("[ Standby ]", "Waiting button..", f"Sent: #{press_count}", "Press to upload")


def main():
    global press_count

    # 1. 開機歡迎畫面
    display_msg("MCU Sheet Sync", "Booting...", "ESP32-S3")
    time.sleep(1)

    # 2. 自動連線 Wi-Fi (輪詢切換)
    if not auto_connect_wifi():
        print("Wi-Fi 無法建立連線，停止執行。")
        return

    # 3. 進入待機畫面
    show_standby()

    last_btn_state = 1

    # 4. 主按鍵監聽迴圈
    while True:
        btn_state = button.value()

        # 偵測由 1 (放開) 變成 0 (按下) 的負緣觸發
        if last_btn_state == 1 and btn_state == 0:
            time.sleep_ms(30)  # 軟體防彈跳 (Debounce)
            if button.value() == 0:
                press_count += 1
                print(f"\n🔘 偵測到按鍵按下！第 {press_count} 次觸發")

                # 送出資料
                send_data_to_sheet(press_count)

                # 重返待機畫面
                show_standby()

        last_btn_state = btn_state
        time.sleep_ms(20)


if __name__ == '__main__':
    main()
