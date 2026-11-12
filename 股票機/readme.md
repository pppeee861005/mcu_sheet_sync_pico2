# 股票機開發計劃與系統規格 (README)

本專案為基於 **Raspberry Pi Pico 2 W** 的輕量化物聯網「台股大盤即時監控機」。
透過 **Google Apps Script (GAS)** 雲端中繼，參考 `stocks.py` 爬取台灣證券交易所 (TWSE) 大盤數據，經由精簡 REST API 傳輸至 Pico 2 W，並於 **LCD1602 (I2C)** 螢幕上顯示當日大盤加權指數與漲跌點數。

---

## 📌 開發目標與架構

```
+---------------------+       HTTP GET (JSON)       +-------------------------+
| 台灣證券交易所 (TWSE) | <========================> | Google Apps Script(GAS) |
| FMTQIK 盤後/即時資料 |                             | 執行 stocks.py 爬蟲邏輯  |
+---------------------+                             +-------------------------+
                                                                 ▲
                                                                 │ HTTPS REST (精簡JSON)
                                                                 ▼
                                                    +-------------------------+
                                                    |  Raspberry Pi Pico 2 W  |
                                                    |  (MicroPython 韌體)     |
                                                    +-------------------------+
                                                                 │ I2C (GP0/GP1)
                                                                 ▼
                                                    +-------------------------+
                                                    |     LCD1602 顯示螢幕     |
                                                    | TAIEX:  23,522.53       |
                                                    | CHG:    +148.87  ▲      |
                                                    +-------------------------+
```

---

## 🛠 硬體配置 (同 `mcu_sheet_sync_pico2`)

- **主控制器**：Raspberry Pi Pico 2 W (RP2350 Wi-Fi, 3.3V 邏輯)
- **顯示模組**：LCD1602 + PCF8574 I2C 轉接板
  - `GND` $\rightarrow$ Pico 2 W **Pin 38 (GND)**
  - `VCC` $\rightarrow$ Pico 2 W **Pin 40 (VBUS, 5V 供電，防止背光與對比不足)**
  - `SDA` $\rightarrow$ Pico 2 W **Pin 1 (GP0, I2C0 SDA)**
  - `SCL` $\rightarrow$ Pico 2 W **Pin 2 (GP1, I2C0 SCL)**
- **實體按鍵 (選配)**：
  - 按鍵 1 $\rightarrow$ Pico 2 W **Pin 19 (GP14)**（手動強制刷新最新行情）
  - 按鍵 2 $\rightarrow$ Pico 2 W **Pin 21 (GP16)**（切換背光或切換資訊顯示）

---

## 📡 軟體與爬蟲設計 (參考 `stocks.py`)

### 1. 爬蟲邏輯 (參考 `stocks.py` 之 `index_info()`)
- **TWSE 大盤 API 端點**：
  `https://www.twse.com.tw/rwd/zh/afterTrading/FMTQIK?date={YYYYMM01}&response=json`
- **解析核心欄位**：
  1. `日期` (Date)
  2. `發行量加權股價指數` (TAIEX Index)
  3. `漲跌點數` (Change Point，含正負符號)
- **雲端處理**：由 Google Apps Script 定時或隨呼叫抓取最新交易日資料，過濾掉多餘歷史紀錄，回傳輕量 JSON：
  ```json
  {
    "status": "success",
    "date": "113/11/11",
    "index": "23522.53",
    "change": "+148.87",
    "direction": "UP"
  }
  ```

### 2. MicroPython 韌體端流程 (`main.py`)
1. **開機自檢**：I2C 掃描 LCD1602 位址（預設 `0x27`），顯示開機與 Wi-Fi 連線畫面。
2. **多 SSID 自動容錯連線**（`config.py`）：優先連接手機熱點，斷線自動切換家用 Wi-Fi。
3. **週期性數據更新**：
   - 每 3~5 分鐘透過 HTTPS 向 GAS 取得最新大盤點數。
   - 內建重試與異常防護機制，避免斷網死機。
4. **LCD1602 專屬排版**（16 字元 × 2 行）：
   - 第一行：`TAIEX: 23522.53`
   - 第二行：`CHG:   +148.87  ▲` (自定義自型繪製 ▲ 漲 / ▼ 跌符號)

---

## 📅 開發階段與里程碑

- [x] **階段一：環境分析與硬體相依庫齊備**
  - 確認 LCD 驅動 (`lcd_api.py`, `pico_i2c_lcd.py`)。
  - 確認 Wi-Fi 配置文件 (`config.py`)。
- [ ] **階段二：Google Apps Script (GAS) 爬蟲中繼部署**
  - 移植 `stocks.py` 核心邏輯至 GAS (`google_apps_script.js`)。
  - 驗證 Web App 部署與 JSON 輸出格式。
- [ ] **階段三：Pico 2 W 韌體核心撰寫 (`main.py`)**
  - 實作自定義漲跌箭頭自型 (Custom Characters)。
  - 實作多 Wi-Fi 連線與 HTTPS 資料同步循環。
  - 整合 GP14 按鍵支援隨按隨刷。
- [ ] **階段四：實機燒錄與整合驗證**
  - 使用 `mpremote` 上傳至硬體實體測試。
