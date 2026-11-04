# Pico 2 W + LCD1602 智慧多系統終端 (含 AI 智慧農業)

本專案為 **Raspberry Pi Pico 2 W** 與 **LCD1602** 專屬的物聯網終端系統。
內建儀式感開機動畫、MicroPython 原生防碎片 HTTPS 核心，整合 Google Apps Script (GAS) 雲端試算表與 **Google Gemini Flash AI** 雲端推理。

---

## 一、硬體接線表

| 元件 | 模組腳位 | Pico 2 W 腳位 | 備註 |
| :--- | :--- | :--- | :--- |
| **LCD1602 (I2C / PCF8574)** | **GND** | **GND** (Pin 38) | 共地 (Common Ground) |
| | **VCC** | **VBUS** (Pin 40) | **5V 供電** (對比度才充足) |
| | **SDA** | **GP0** (Pin 1) | I2C0 SDA (資料線) |
| | **SCL** | **GP1** (Pin 2) | I2C0 SCL (時脈線) |
| **按鈕 1 (Left / Next)** | 一端 | **GP14** (Pin 19) | 內建上拉，按下接地 |
| | 另一端 | **GND** (Pin 18) | |
| **按鈕 2 (Right / Enter)** | 一端 | **GP16** (Pin 21) | 內建上拉，按下接地 |
| | 另一端 | **GND** (Pin 23) | |

> [!NOTE]
> LCD1602 背面的可變電阻需微調至字元清晰可見。LCD 螢幕顯示**一律規範為純英文**。

---

## 二、四大子系統使用說明

開機完成 Wi-Fi 連線後進入主選單：
- **按 Left (GP14)**：切換下一個系統（`1 -> 2 -> 3 -> 4` 循環）。
- **按 Right (GP16)**：確認進入該系統。

```
+-------------------------------------------------------------+
|                      [主選單 (Main Menu)]                    |
|   > 1.Fortune Dice  /  > 2.CloudMsg  /  > 3.Sheet Sync     |
|   > 4.AI Agri (智慧農業灌溉決策)                              |
+-------------------------------------------------------------+
```

### 1. Fortune Dice（命運籤筒與午餐選擇機）
- **Left (Preset)**：隨機抽取本機預設籤筒（拉霸減速動畫與背光閃爍神諭）。
- **Right (Cloud)**：連線 Google 試算表抓取自訂選單並隨機抽取。
- 推理/抽取結果會自動銘刻至雲端試算表留存。

### 2. CloudMsg（雲端留言看板）
- **Left (Pull)**：純讀取雲端最新留言。若超過 16 字元會啟動**跑馬燈平滑捲動**。
- **Right (Push)**：從本機隨機挑選一句極客英文金句發布到試算表。

### 3. Sheet Sync（上報計數同步）
- **Left (+1)**：本地累積次數加一。
- **Right (Push)**：將累積次數上傳至試算表儲存。

### 4. AI Agri（AI 智慧農業灌溉決策）
- **Right (Run)**：啟動 AI 決策流程：
  1. **資料檢驗**：向試算表檢查 E 欄農田感測指標。若無數據或欄位未填，LCD 第二行直接打印 `No_data` 並安全返回。
  2. **AI 推理**：呼叫 Gemini Flash 模型進行智慧判斷，LCD 顯示 `AI Thinking...`。
  3. **決策呈現**：
     - 第一行：`>> WATER NOW <<` 或 `>> NO WATER <<`
     - 第二行：英文簡短原由（如 `Very dry soil`，≤ 16 字元）。
  4. **雲端存證**：自動將決策與環境數據寫入試算表 `FarmLogs` 分頁。

---

## 三、Google 試算表設定規範 (針對 AI Agri)

系統採用 **E 欄最新有效資料讀取** 機制：

### 1. `FarmData` 工作表 (輸入表)
在 Google 試算表的 **E 欄** 依序填入 5 項環境指標（以逗號分隔）：
* **E1 (標題定義)**：
  `空氣濕度(%),氣溫(C),土壤乾度(%),土壤EC,降雨預報`
* **E2 (最新數據範例)**：
  `48, 25.5, 80, 1.3, No Rain`

> **五大參數順序**：
> 1. 空氣濕度 (%)
> 2. 氣溫 (°C)
> 3. 土壤乾度 (%，數值愈高愈乾燥)
> 4. 土壤 EC 值 (電解質/肥力)
> 5. 降雨預報 (`No Rain` / `Rain Soon` / `Sunny`)

### 2. `FarmLogs` 工作表 (日誌表)
由系統自動建立，每次 Pico 2 W 推理完成後會自動新增一筆紀錄：
`[時間戳記, 裝置名稱, 決策動作, 決策原由, 空氣濕度, 氣溫, 土壤乾度, 土壤EC, 降雨預報]`

---

## 四、檔案結構與快速部署

```text
├── .env                     # 存放 GOOGLE_API_KEY
├── config.py                # Wi-Fi 與 GAS Script ID 配置
├── google_apps_script.js    # Google Apps Script 雲端後端程式碼
├── lcd_api.py               # LCD1602 抽象指令層
├── pico_i2c_lcd.py          # Pico I2C 驅動
├── main.py                  # 四合一核心韌體 (MicroPython)
├── README.md                # 專案總覽與使用說明
├── 系統三開發計劃.md        # 系統三規格書
├── 開發進度追蹤表.md        # 里程碑驗證記錄
└── 農場數據試算表範例.md    # 試算表範例指南
```

### 使用 `mpremote` 快速上傳至 Pico 2 W：
```powershell
# 上傳驅動與配置檔
python -m mpremote connect COM<埠號> cp .env :.env + cp config.py :config.py + cp lcd_api.py :lcd_api.py + cp pico_i2c_lcd.py :pico_i2c_lcd.py

# 上傳核心主程式並自動重啟
python -m mpremote connect COM<埠號> cp main.py :main.py + reset
```
