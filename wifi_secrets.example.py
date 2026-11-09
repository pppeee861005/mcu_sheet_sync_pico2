# wifi_secrets.example.py
# 使用說明:
# 1. 複製此檔為 wifi_secrets.py (此檔已被 .gitignore 忽略，不會被推上 GitHub)
# 2. 填入您的手機熱點與家用 Wi-Fi 帳號密碼
# 3. 燒錄至 MCU: python -m mpremote connect <COM_PORT> cp wifi_secrets.py :wifi_secrets.py

WIFI_NETWORKS = [
    {"ssid": "YOUR_PHONE_HOTSPOT", "password": "YOUR_PASSWORD"},  # 手機熱點 (優先順序 1)
    {"ssid": "YOUR_HOME_WIFI",     "password": "YOUR_PASSWORD"},  # 家用 Wi-Fi (優先順序 2)
]
