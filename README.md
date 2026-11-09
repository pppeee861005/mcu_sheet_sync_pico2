# 🛠️ 創客工坊 (Maker Monorepo)

這是一個以 **ESP32** 與 **Raspberry Pi Pico (MicroPython)** 為主的個人創客專案庫與自製硬體實作寶典。包含離線掌機、AIoT 智慧聯網裝置、教學課程紀錄及各種趣味硬體實驗。

---

## 🗂️ 專案總覽導覽 (Project Directory Index)

| 分類 | 專案名稱 | 主要晶片 / 核心 | 說明簡介 |
| :--- | :--- | :--- | :--- |
| **🎮 掌機與遊戲** | [終極極客掌機](file:///終極極客掌機/README.md) | ESP32 / OLED / 蜂鳴器 | SkyDeck OS 離線掌機（小恐龍、貓咪餐券、番茄鐘、碼表） |
| | [餐券遊戲機](file:///餐券遊戲機) | Pico / OLED | 經典貓咪實體撕票動畫模擬機 |
| | [Pico 小恐龍 Dino Game](file:///Pico%20小恐龍%20Dino%20Game) | Pico / OLED | 獨立單機版離線小恐龍躲障礙遊戲 |
| | [台彩極客掌機](file:///台彩極客掌機) | ESP32 / OLED | 大樂透 / 威力彩極客隨機選號器 |
| | [自制game boy](file:///自制game%20boy) | ESP32 / Pico | 懷舊掌機自製原型 |
| **🌐 AIoT 智慧家居與音箱** | [智慧音箱](file:///智慧音箱) | ESP32 + Vercel Python API | 智慧語音、雲端 API 整合、天氣與日常助手 |
| | [智慧家居](file:///智慧家居) | ESP32 / MQTT / HTTP | 家庭環境感測與遠端家電控制模組 |
| | [ai ot](file:///ai%20ot) | ESP32 / Pico | AI 雷達警戒燈、物聯網 LED 遠端通信模組 |
| | [mcu_sheet_sync_pico2](file:///mcu_sheet_sync_pico2) | Pico 2 W / GAS | MCU 感測器資料自動上傳 Google Sheets 雲端試算表 |
| **🤖 機器人與自動化** | [自動化植物工廠](file:///自動化植物工廠) | ESP32 / 溫濕度 / 繼電器 | 自動澆水、補光與環境參數調控系統 |
| | [農夫機器人](file:///農夫機器人) | MCU | 農業環境巡邏與自動化感測原型 |
| | [倒車雷達](file:///倒車雷達) | 超音波 / 蜂鳴器 / LED | 距離偵測與多段音效距離警示雷達 |
| | [淹水感知機](file:///淹水感知機) | 水位感測 / 警報 | 實時積水感測與緊急警報器 |
| **📚 課程與教學筆記** | [Mcu課程](file:///Mcu課程) | Pico / ESP32 | 入門至進階課綱（PWM、I2C、ADC 旋鈕、呼吸燈、中斷） |
| | [如何用prompt](file:///如何用prompt) | AI Prompting | 創客與 Agentic Coding 提示詞工程心法 |

---

## ⚡ 常用開發指南 (Quick Reference)

本倉庫使用統一的 MicroPython 工具鏈進行開發：

### 1. 偵測裝置連接埠
```powershell
python -m mpremote devs
```

### 2. 燒錄檔案並重啟板子
```powershell
python -m mpremote connect <COM_PORT> cp <主程式.py> :main.py + reset
```

### 3. 開啟即時 REPL 互動終端
```powershell
python -m mpremote connect <COM_PORT> repl
```

---

## 📌 版本控制規範 (Commit Guidelines)
每次提交時，請遵循 **`[專案名稱] 簡述修改內容`** 的格式，以保持歷史紀錄整潔，例如：
- `git commit -m "[終極極客掌機] 新增按鍵音效反饋"`
- `git commit -m "[智慧音箱] 更新天氣查詢 API 接口"`
