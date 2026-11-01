# README.md - Pico 2 W + LCD1602 Google Sheet 同步機

## 專案簡介
本專案為 `mcu_sheet_sync` 的 **Raspberry Pi Pico 2 W** 與 **LCD1602** 專屬移植版本。
透過 Wi-Fi 連線與 Google Apps Script (GAS) 進行雲端試算表雙向同步。

---

## 硬體接線表

| 元件 | 模組腳位 | Pico 2 W 腳位 | 備註 |
| :--- | :--- | :--- | :--- |
| **LCD1602 (I2C)** | **GND** | **GND** (Pin 38) | 共地 (Common Ground) |
| | **VCC** | **VBUS** (Pin 40) | **5V 供電** (對比度才足夠) |
| | **SDA** | **GP0** (Pin 1) | I2C0 SDA (資料線) |
| | **SCL** | **GP1** (Pin 2) | I2C0 SCL (時脈線) |
| **按鈕 1 (Next / +)** | 一端 | **GP14** (Pin 19) | 內建上拉，按下接地 |
| | 另一端 | **GND** (Pin 18) | |
| **按鈕 2 (Enter / Sync)** | 一端 | **GP16** (Pin 21) | 內建上拉，按下接地 |
| | 另一端 | **GND** (Pin 18/23) | |

---

## 軟體架構
- [lcd_api.py](file:///D:/練習操作區/創客/mcu_sheet_sync_pico2/lcd_api.py)：LCD 命令層。
- [pico_i2c_lcd.py](file:///D:/練習操作區/創客/mcu_sheet_sync_pico2/pico_i2c_lcd.py)：Pico PCF8574 專用驅動。
- [google_apps_script.js](file:///D:/練習操作區/創客/mcu_sheet_sync_pico2/google_apps_script.js)：GAS 雲端後端。
- `config.py`：Wi-Fi SSID/密碼與 GAS Script ID 設定。
- `main.py`：Pico 2 W 專用雙向同步與 16x2 LCD UI 介面。
