# Pico 小恐龍 Dino Game

ESP32-S3 DevKitC-1 + MicroPython 的 OLED 小恐龍遊戲正式版。

## 硬體接線

| 元件 | ESP32-S3 DevKitC-1 |
|---|---|
| OLED SDA | GPIO21 |
| OLED SCL | GPIO22 |
| OLED VCC | 3V3 |
| OLED GND | GND |
| 跳躍按鈕 | GPIO18，另一端接 GND |

OLED 使用 128×64 SSD1306 I²C 模組。按鈕使用內建上拉電阻，按下會觸發跳躍；Game Over 後按下按鈕會重新開始。

## 上傳與執行

需要已安裝 MicroPython 的開發板與 `mpremote`：

```powershell
mpremote connect list
mpremote connect COM3 fs cp ssd1306.py :ssd1306.py
mpremote connect COM3 fs cp main.py :main.py
mpremote connect COM3 reset
```

將 `COM3` 替換為實際序列埠。上傳前可執行：

```powershell
python -m py_compile main.py
```

## 遊戲功能

- 按鈕跳躍與重力效果
- 隨機仙人掌障礙物與碰撞判定
- 即時分數、最高分與 Game Over 畫面
- 分數增加後障礙物速度提高
- 開始畫面與重新開始提示

## 專案文件

- `開發進度追蹤表.md`：版本里程碑與實體測試紀錄
- `main.py`：遊戲主程式
- `ssd1306.py`：OLED 驅動程式
- `AGENTS.md`：貢獻與開發規範
