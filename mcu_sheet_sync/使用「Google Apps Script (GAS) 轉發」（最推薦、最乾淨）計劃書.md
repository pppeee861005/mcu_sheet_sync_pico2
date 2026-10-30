# MCU 與 Google 試算表通訊計畫書：Google Apps Script (GAS) 轉發方案

## 1. 專案背景與目標

- **目標**：讓 MicroPython 單晶片（如 ESP32 / Pico W）通電開機後，自動連接 Wi-Fi，並將感測數據或開機紀錄寫入指定的 Google 試算表（Google Sheets）。
- **架構優勢**：
  - **免肥大憑證**：MicroPython 記憶體有限，無法負荷 Google 官方龐大的 OAuth 2.0 / RSA 加密套件（如 `gspread`）。
  - **極簡請求**：MCU 僅需透過輕量的 `urequests` 發送單一 HTTP POST/GET 請求。
  - **安全性與彈性**：憑證由 Google 內建的 Google Apps Script (GAS) 內部處理，MCU 不需要內嵌高風險金鑰檔案。

---

## 2. 系統架構流程圖

```text
┌──────────────────────┐
│  ESP32 / MCU         │
│  (MicroPython)       │
│                      │
│  1. 開機通電          │
│  2. 連接 Wi-Fi       │
│  3. 讀取感測/時間狀態 │
│  4. 發送 HTTP POST   │
└──────────┬───────────┘
           │
           │  JSON 數據 (例如: { "temp": 28.5, "humidity": 65, "status": "Boot OK" })
           ▼
┌──────────────────────────────────────┐
│  Google Apps Script (GAS Web App)    │
│  - 部署為公開 Web 應用程式            │
│  - doPost(e) 解析接收到的 JSON 參數  │
└──────────┬───────────────────────────┘
           │
           │  appendRow()
           ▼
┌──────────────────────────────────────┐
│  Google Sheets (雲端試算表)          │
│  自動追加寫入新資料列 (即時更新)     │
└──────────────────────────────────────┘
```

---

## 3. Google 端設定步驟 (Google Apps Script)

### 步驟 3.1：建立 Google 試算表
1. 打開 Google Drive，建立一份新的 Google 試算表（例如命名為：`農夫機器人_MCU記錄表`）。
2. 在第 1 列設定標題欄位：
   - A1: `時間戳記`
   - B1: `裝置名稱`
   - C1: `溫度`
   - D1: `濕度`
   - E1: `備註 / 狀態`

### 步驟 3.2：編寫 Google Apps Script 腳本
1. 點擊頂部選單 **擴充功能 (Extensions) -> Apps Script**。
2. 清除預設內容，貼上以下 Apps Script 程式碼：

```javascript
function doPost(e) {
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    var data = JSON.parse(e.postData.contents);
    
    // 取得當前時間
    var timestamp = new Date();
    
    // 依序寫入新的一列
    sheet.appendRow([
      timestamp,
      data.device || "ESP32_Device",
      data.temp || "",
      data.humidity || "",
      data.message || "Boot Success"
    ]);
    
    return ContentService.createTextOutput(JSON.stringify({
      "status": "success",
      "message": "Data appended successfully"
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({
      "status": "error",
      "error": err.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}
```

### 步驟 3.3：發布與取得 Web 應用程式網址 (重要)
1. 點擊右上角 **部署 (Deploy) -> 新增部署作業 (New deployment)**。
2. 齒輪圖示選擇 **網頁應用程式 (Web app)**：
   - **說明 (Description)**：`MCU Data Logger API`
   - **執行身分 (Execute as)**：`我 (Me / 你的 Google 帳號)`
   - **誰可以存取 (Who has access)**：**`所有人 (Anyone)`** *(重要：這樣 MCU 才能無阻礙免登入送出資料)*
3. 點擊 **部署**，初次部署時依畫面指示授予 Google 帳號授權。
4. 複製生成的 **網頁應用程式網址 (Web App URL)**（格式通常為：`https://script.google.com/macros/s/AKfycb.../exec`）。

---

## 4. MCU 端實作計畫 (MicroPython)

### 檔案規劃
- [`boot.py`](file:///D:/練習操作區/創客/mcu_sheet_sync/boot.py)：（可選）基礎網路環境初始化。
- [`main.py`](file:///D:/練習操作區/創客/mcu_sheet_sync/main.py)：MCU 核心開機腳本（連線 Wi-Fi、發送請求至 GAS、可在 OLED 上顯示狀態）。
- [`ssd1306.py`](file:///D:/練習操作區/創客/mcu_sheet_sync/ssd1306.py)：現有 OLED 螢幕驅動（可選，提供視覺回饋）。

### MCU 程式邏輯概要 (`main.py`)
```python
import network
import urequests
import ujson
import time

# 1. Wi-Fi 設定
SSID = "您的_WIFI_名稱"
PASSWORD = "您的_WIFI_密碼"

# 2. Google Apps Script 網頁應用程式網址
GAS_URL = "https://script.google.com/macros/s/您的部署ID/exec"

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("連線至 Wi-Fi 中...")
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            time.sleep(0.5)
            print(".", end="")
    print("\nWi-Fi 連線成功，IP:", wlan.ifconfig()[0])

def send_to_sheet():
    payload = {
        "device": "Farmer_ESP32_01",
        "temp": 26.8,
        "humidity": 68.2,
        "message": "MCU 開機通電記錄成功"
    }
    
    headers = {"Content-Type": "application/json"}
    print("正在上傳資料至 Google Sheet...")
    
    try:
        response = urequests.post(GAS_URL, data=ujson.dumps(payload), headers=headers)
        print("回應狀態碼:", response.status_code)
        print("回應內容:", response.text)
        response.close()
    except Exception as e:
        print("發送失敗:", e)

# 主流程
connect_wifi()
send_to_sheet()
```

---

## 5. 燒錄與驗證流程

1. **環境檢查**：
   - 透過 PowerShell 確認已偵測到 MCU 序列埠（例如 `COM4`）：
     ```powershell
     mpremote devs
     ```
2. **上傳程式碼到 MCU**：
   - 使用現有的 `pico-micropython-flash` 技能規範，透過 `mpremote` 傳輸：
     ```powershell
     mpremote connect COM4 cp main.py :main.py
     ```
3. **通電重啟測試**：
   - 重新啟動 MCU：
     ```powershell
     mpremote connect COM4 reset
     ```
   - 觀察串列監視器輸出，並打開 Google 試算表確認新資料行是否自動寫入。

---

## 6. 里程碑進度表

- [x] **M0**：評估與架構確立（排除高資源耗損的 OAuth 直接通訊，採用 GAS 方案）。
- [x] **M1**：建立專案計劃書與標準架構規格（本文件）。
- [ ] **M2**：使用者於 Google 試算表建立 GAS Web App 並取得專屬 API 網址。
- [ ] **M3**：建立客製化 MicroPython `main.py`（整合 Wi-Fi 與 GAS 傳輸，並加入 OLED 開機狀態顯示）。
- [ ] **M4**：利用 `mpremote` 燒錄至硬體設備（COM4）並完成開機寫入測試。
