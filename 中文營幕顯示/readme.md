# 中文螢幕顯示 (Chinese OLED Display System)

本專案目錄依據 [`終極極客掌機/硬體架構.md`](file:///d:/練習操作區/創客/終極極客掌機/硬體架構.md) 的規範進行建置，採用 **ESP32-S3 DevKitC-1** 主控板，搭配 **0.96 吋 SSD1306 OLED (128x64)**，實現 MicroPython 環境下的繁體中文 16x16 點陣字型渲染、頁面輪播與雙實體按鍵互動。

---

## 1. 硬體接線腳位規範 (完全對齊終極極客掌機)

| 週邊元件 | 元件引腳 | ESP32-S3 腳位 | 模式 / 說明 |
| :--- | :--- | :--- | :--- |
| **0.96 吋 OLED (SSD1306)** | **VCC** | **3V3** | 3.3V 電源 |
| | **GND** | **GND** | 系統共地 |
| | **SDA** | **GPIO 21** | I²C 資料線 (400kHz) |
| | **SCL** | **GPIO 22** | I²C 時脈線 |
| **實體按鈕 A (左鍵)** | 一端接腳位，一端接 GND | **GPIO 18** | `Pin.IN, Pin.PULL_UP`，按下為 0 (切換頁面) |
| **實體按鈕 B (右鍵)** | 一端接腳位，一端接 GND | **GPIO 4** | `Pin.IN, Pin.PULL_UP`，按下為 0 (確認/反白提示) |
| **有源蜂鳴器** | 正極 (+)，負極接 GND | **GPIO 33** | `Pin.OUT`，按鍵音效提示 |
| **板載 LED** | 內建 LED | **GPIO 2** | `Pin.OUT`，按鍵同步燈效 |

---

## 2. 專案檔案清單

```text
d:\練習操作區\創客\中文營幕顯示\
├── fonts_cn.py          # 16x16 繁體中文字型庫與點陣渲染函式
├── ssd1306.py           # SSD1306 I2C OLED 驅動程式
├── main.py              # 繁體中文介面、頁面輪播與按鍵互動主程式
├── 硬體架構.md          # 掌機接線拓撲與硬體規格手冊
└── readme.md            # 專案說明文件
```

---

## 3. 中文渲染原理

MicroPython 內建的 `oled.text()` 僅支援 8x8 ASCII 英數字元。本專案透過 [`fonts_cn.py`](file:///d:/練習操作區/創客/中文營幕顯示/fonts_cn.py)：
1. 建立 16x16 繁體漢字點陣庫（每字 32 bytes）。
2. 提供 `draw_char_16x16()` 與 `draw_string_cn()` 函式，自動混排 16x16 漢字與 8x8 英文字串。
3. 支援換行與超出螢幕邊界的自動折行。

---

## 4. 燒錄與執行指令

若要燒錄至 ESP32-S3 開發板（COM 埠以實際連接為準，如 COM3 或 COM4）：

```powershell
cd "d:\練習操作區\創客\中文營幕顯示"
python -m mpremote connect <COM_PORT> cp fonts_cn.py : + cp ssd1306.py : + cp main.py : + reset
```
