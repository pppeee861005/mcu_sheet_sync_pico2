# config.py - Wi-Fi 與 Google Apps Script / Gemini 設定檔

WIFI_NETWORKS = [
    {"ssid": "Redmi 13C", "password": "chdmchkcrdfd7e8"},  # 手機熱點 (優先)
    {"ssid": "egg5630",   "password": "27985630"}          # 家用 Wi-Fi (備援)
]

# 最新 Google Apps Script 佈署識別碼 (股票機大盤爬蟲端點)
GAS_SCRIPT_ID = "AKfycbxKgoNQivz1UFoJOTgo7-axxLaGGhfKfXPyfWXZvjjdegiBQ1yYGCR08xNeEe64ifljvg"

# 動態從 .env 讀取 GOOGLE_API_KEY
GOOGLE_API_KEY = ""
try:
    with open(".env", "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("GOOGLE_API_KEY"):
                parts = line.split("=", 1)
                if len(parts) == 2:
                    GOOGLE_API_KEY = parts[1].strip().strip('"').strip("'")
                    break
except Exception:
    pass

if not GOOGLE_API_KEY:
    # 預設金鑰需於 .env 中設定 GOOGLE_API_KEY
    GOOGLE_API_KEY = ""
