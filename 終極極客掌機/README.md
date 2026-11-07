# MCU 与 Google 試算表通訊與同步 (mcu_sheet_sync)

本專案目錄專注於實現 **微控制器（MCU，如 ESP32、Raspberry Pi Pico W）** 與 **Google 試算表（Google Sheets）** 之間的資料通訊、感測記錄與狀態同步。

---

## 💡 心路歷程：架構演進與技術選型

> **原本要把「操作 Google Sheet 的 Python 程式」直接放入 MCU 中來通訊，但是 AGY 建議在 Google 端使用 JavaScript (Google Apps Script, GAS) 轉發，MCU 只需要發出一道簡單的 HTTP POST 即可。**
>
> 這樣一來，MCU 中的程式變得極為精簡小巧，徹底擺脫了肥大無法執行的 OAuth RSA 憑證套件，改用 AGY 建議的方案進行開發。這也是目前物聯網 (IoT) 連接 Google 服務的主流最佳解法。

---

## 📁 目錄檔案清單與說明

| 檔案名稱 | 說明 |
| :--- | :--- |
| **`README.md`** | 本專案總覽與架構說明文件（含心路歷程）。 |
| **`操作手冊與燒錄指南.md`** | 完整 SOP 指南，從 Google Apps Script 雲端部屬到 `mpremote` 燒錄步驟。 |
| **`任務需求書.md`** | 定義 MCU 開機待機、雙 Wi-Fi 自動輪詢與實體按鍵觸發寫入的規格。 |
| **`硬體架構.md`** | ESP32-S3 DevKitC-1、SSD1306 OLED 與實體按鈕接線圖及 Pinout。 |
| **`MCU 端的 Wi-Fi 設定.md`** | 家用 Wi-Fi (`egg5630`) 與手機熱點 (`Redmi 13C`) 帳密與自動連線程式碼。 |
| **`開發計劃書.md`** | 專案里程碑 (M0~M4) 與架構規範。 |
| **`開發進度追蹤表.md`** | 任務進度 Check-list 與實體板測試 Log。 |
| **`main.py`** | MCU MicroPython 主程式（開機 ➔ 待機 ➔ 按鍵 POST ➔ 寫入試算表）。 |
| **`ssd1306.py`** | 修正過 COM 腳位設定的 128x64 OLED 顯示器驅動。 |
| **`google_apps_script.js`** | 貼在 Google 試算表端的 JavaScript (GAS) 轉發程式碼。 |
| **`google_sheet_oauth.py`** | 電腦版 Python (CPython) 範例（使用 `gspread` 與 Service Account 金鑰）。 |
| **`「豪力的api_ipynb」的副本.ipynb`** | 原始學習講義 Notebook（包含 JSON、API、OAuth 等章節）。 |

---

## 🚀 核心工作流程與架構

```text
[ MCU 端 (ESP32 / Pico W) ]
         │ (Wi-Fi 連線)
         ▼
[ HTTP POST JSON 數據 ]
         │
         ▼
[ Google Apps Script (GAS) Web App ]
         │ (自動解析並追加新列)
         ▼
[ Google Sheets 雲端試算表 ]
```

1. **為什麼不直接在 MCU 跑 OAuth？**
   - MicroPython 記憶體與算力有限，無法直接執行肥大的 RSA/JWT 加密與 Google 官方 `gspread` 套件。
2. **最佳實踐**：
   - 透過 Google 免費提供的 **Apps Script** 發布為公開 Web API，MCU 僅需以輕量的 `urequests.post()` 發送 JSON 數據即可完成寫入。

---

## 🛠️ 常用燒錄與除錯工具

本專案支援以 `mpremote` 進行指令列程式碼燒錄：
```powershell
# 1. 偵測連接埠
mpremote devs

# 2. 將 main.py 上傳至 MCU 根目錄
mpremote connect COM4 cp main.py :main.py

# 3. 軟體重開機以執行
mpremote connect COM4 reset
```
