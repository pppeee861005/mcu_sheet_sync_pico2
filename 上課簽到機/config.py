# config.py - 上課簽到機 Wi-Fi 與 Google Apps Script 設定檔 (v2.0 支援繁體中文名單)

# Wi-Fi 多組 SSID 優先順序設定 (手機熱點優先，家用 Wi-Fi 備援)
WIFI_NETWORKS = [
    {"ssid": "Redmi 13C", "password": "chdmchkcrdfd7e8"},  # 手機熱點 (優先)
    {"ssid": "egg5630",   "password": "27985630"}          # 家用 Wi-Fi (備援)
]

# Google Apps Script 簽到表記錄端點 ID
GAS_CHECKIN_SCRIPT_ID = "AKfycbxsDRli36NtvJZlqIglqQKhy5ooRH1GtL_dt253pu9hJ5Trv_AMMjIrBMMD40Eo5UKC"

# 繁體中文學生名單
STUDENT_LIST = [
    "陳大明",
    "林小美",
    "王大維",
    "張志豪",
    "黃雅婷",
    "李冠宇",
    "吳家豪",
    "蔡佩君"
]
