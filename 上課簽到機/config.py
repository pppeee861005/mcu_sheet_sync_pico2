# config.py - 上課簽到機 Wi-Fi 與 Google Apps Script 設定檔 (雙班級管理版)

# Wi-Fi 多組 SSID 優先順序設定 (手機熱點優先，家用 Wi-Fi 備援)
WIFI_NETWORKS = [
    {"ssid": "Redmi 13C", "password": "chdmchkcrdfd7e8"},  # 手機熱點 (優先)
    {"ssid": "egg5630",   "password": "27985630"}          # 家用 Wi-Fi (備援)
]

# Google Apps Script 簽到表記錄端點 ID
GAS_CHECKIN_SCRIPT_ID = "AKfycbxsDRli36NtvJZlqIglqQKhy5ooRH1GtL_dt253pu9hJ5Trv_AMMjIrBMMD40Eo5UKC"

# 雙班級架構配置
CLASSES = {
    "AIoT實戰班": [
        "講師 賴建安",
        "繆志煜",
        "張元俊",
        "黃學豪",
        "張軒翟",
        "劉浩萱",
        "彭清波",
        "洪瑞雄",
        "黃國峰",
        "黃煜仁",
        "許秩赫",
        "余姮",
        "黃雅婷",
        "謝旻珊",
        "林威達",
        "張祥禔",
        "許玉詩",
        "游建益",
        "施彤霖",
        "吳逸盈",
        "黃玠翔",
        "許陳候",
        "晁成雯",
        "陳一銘"
    ],
    "開心農場班": [
        "講師 賴建安",
        "陳大明",
        "林小美",
        "王大維",
        "張志豪",
        "李冠宇",
        "吳家豪",
        "蔡佩君"
    ]
}
