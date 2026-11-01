# LCD1602 (I²C) 學習筆記與教學

## 1. 硬體介紹
LCD1602 是一款能顯示 **2 行、每行 16 個英文字元/數字/符號** 的點陣液晶模組。
傳統 1602 需要接 16 根針腳（佔用過多 GPIO），我們搭配的 **PCF8574 轉接板** 透過 I²C 協定將控制線縮減到 **4 條線**。

---

## 2. 接線表 (Raspberry Pi Pico)

| LCD1602 (I2C 背板) | Pico 腳位 | 實體引腳編號 (Pin) | 說明 |
| :--- | :--- | :--- | :--- |
| **GND** | **GND** | Pin 38 (或任一 GND) | 接地 |
| **VCC** | **VBUS** | **Pin 40** | **5V 供電** (若接 3V3 對比度太低會看不到字) |
| **SDA** | **GP0** | Pin 1 | I2C0 數據線 (負責傳送資料) |
| **SCL** | **GP1** | Pin 2 | I2C0 時脈線 (負責打節拍) |

> ⚠️ **重要除錯提示**：
> 1. **畫面只有背光亮，看不到字**：請拿一字起子微調 LCD 背板上的「藍色可調電阻（對比度調節）」。
> 2. **跳出找不到裝置**：檢查杜邦線接觸是否良好，以及 VCC 是否接在 5V (VBUS)。

---

## 3. 檔案結構

在目錄 `D:\練習操作區\創客\Mcu課程\學習lcd` 中已為您建立好三隻檔案：
1. [lcd_api.py](file:///D:/練習操作區/創客/Mcu課程/學習lcd/lcd_api.py)：LCD 命令庫（通用 API）。
2. [pico_i2c_lcd.py](file:///D:/練習操作區/創客/Mcu課程/學習lcd/pico_i2c_lcd.py)：Pico 專用 I2C LCD 控制驅動。
3. [main.py](file:///D:/練習操作區/創客/Mcu課程/學習lcd/main.py)：主程式（自動掃描 I2C、顯示 Hello Pico 與計數器）。

---

## 4. 常用函式語法

```python
lcd.clear()               # 清除螢幕全部字元
lcd.move_to(col, row)     # 移動游標 (col: 0~15, row: 0~1)
lcd.putstr("Text")        # 在游標當前位置印出字串
lcd.hal_backlight_off()   # 關閉背光
lcd.hal_backlight_on()    # 開啟背光
lcd.show_cursor()         # 顯示底線游標
lcd.hide_cursor()         # 隱藏游標
lcd.blink_cursor_on()     # 開啟游標閃爍
```

---

## 5. 如何上傳到 Pico 執行

使用 Thonny 開啟：
1. 將 `lcd_api.py` 與 `pico_i2c_lcd.py` 儲存/上傳到 Pico 的根目錄 `: /`。
2. 開啟並執行 `main.py`。
