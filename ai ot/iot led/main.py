import network
import time
import requests
import neopixel
from machine import Pin

WIFI_SSID = "egg5630"
WIFI_PASSWORD = "27985630"
HOTSPOT_SSID = "Redmi 13C"
HOTSPOT_PASSWORD = "chdmchkcrdfd7e8"
API_URL = "https://pico-vercel-server-ha114j163-pperters-projects.vercel.app/api/command"

LED_PIN = 0
LED_COUNT = 12
POWER_COLOR = (0, 0, 80)
WIFI_COLOR = (80, 40, 0)
CONNECTED_COLOR = (0, 80, 0)
STANDBY_COLOR = (40, 40, 40)
WIFI_ERROR_COLOR = (80, 0, 80)
ON_COLOR = (80, 0, 0)
OFF_COLOR = (0, 0, 0)

ring = neopixel.NeoPixel(Pin(LED_PIN), LED_COUNT)

def set_ring(color):
    for index in range(LED_COUNT):
        ring[index] = color
    ring.write()

set_ring(POWER_COLOR)
wifi = network.WLAN(network.STA_IF)
wifi.active(True)

def connect_wifi():
    networks = [
        (HOTSPOT_SSID, HOTSPOT_PASSWORD, "phone hotspot"),
        (WIFI_SSID, WIFI_PASSWORD, "home Wi-Fi"),
    ]
    while not wifi.isconnected():
        for ssid, password, name in networks:
            set_ring(WIFI_COLOR)
            print("Connecting to", name, "...")
            wifi.connect(ssid, password)
            for _ in range(15):
                if wifi.isconnected():
                    print("Connected to", name)
                    return
                print("Connecting...")
                time.sleep(1)
            print("Wi-Fi connection failed:", name)
            wifi.disconnect()
            set_ring(WIFI_ERROR_COLOR)
            time.sleep(2)

connect_wifi()
print("Wi-Fi connected!")
set_ring(CONNECTED_COLOR)
time.sleep(1)
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
