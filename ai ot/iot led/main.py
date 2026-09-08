import network
import time
import requests
import neopixel
from machine import Pin


WIFI_SSID = "egg5630"
WIFI_PASSWORD = "27985630"
API_URL = "https://pico-vercel-server-ha114j163-pperters-projects.vercel.app/api/command"

LED_PIN = 0
LED_COUNT = 12

# WS2812 狀態顏色
POWER_COLOR = (0, 0, 80)       # 有電源／啟動中：藍色
WIFI_COLOR = (80, 40, 0)       # 等待 Wi-Fi：黃色
CONNECTED_COLOR = (0, 80, 0)   # Wi-Fi 已連上：綠色
STANDBY_COLOR = (40, 40, 40)   # 待命中：白色
WIFI_ERROR_COLOR = (80, 0, 80) # 無法取得 Wi-Fi：紫色
ON_COLOR = (80, 0, 0)          # 收到 LED_ON：紅色
OFF_COLOR = (0, 0, 0)

ring = neopixel.NeoPixel(Pin(LED_PIN), LED_COUNT)


def set_ring(color):
    for index in range(LED_COUNT):
        ring[index] = color
    ring.write()


# 有電源，開始啟動
set_ring(POWER_COLOR)

wifi = network.WLAN(network.STA_IF)
wifi.active(True)

# 連線失敗時顯示錯誤，並持續重試
while not wifi.isconnected():
    set_ring(WIFI_COLOR)
    wifi.connect(WIFI_SSID, WIFI_PASSWORD)

    for _ in range(15):
        if wifi.isconnected():
            break
        print("Connecting...")
        time.sleep(1)

    if not wifi.isconnected():
        print("Wi-Fi connection failed")
        set_ring(WIFI_ERROR_COLOR)
        time.sleep(5)

print("Wi-Fi connected!")
set_ring(CONNECTED_COLOR)
time.sleep(1)

# Wi-Fi 已連線，等待雲端指令
set_ring(STANDBY_COLOR)

while True:
    response = None
    try:
        response = requests.get(API_URL)
        print("Status:", response.status_code)

        data = response.json()
        command = data.get("command")
        print("Command:", command)

        if command == "LED_ON":
            set_ring(ON_COLOR)
        elif command == "LED_OFF":
            set_ring(OFF_COLOR)
        else:
            set_ring(STANDBY_COLOR)

    except Exception as error:
        print("Error:", error)
    finally:
        if response is not None:
            response.close()

    time.sleep(10)
