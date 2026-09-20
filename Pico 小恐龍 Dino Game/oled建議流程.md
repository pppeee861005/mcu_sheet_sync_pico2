# OLED 建議流程

日後接上或更換 OLED 顯示器時，先完成硬體與座標定位，再開始撰寫遊戲功能。

## 1. 確認硬體規格

確認 OLED 的：

- 解析度：`128x64` 或 `128x32`
- 通訊介面：I²C
- 電源電壓：通常使用 `3V3`
- I²C 位址：通常是 `0x3C` 或 `0x3D`

## 2. 確認接線

本專案使用：

```text
OLED VCC      -> ESP32 3V3
OLED GND      -> ESP32 GND
OLED SDA      -> GPIO21
OLED SCL/SCK  -> GPIO22
```

## 3. 掃描 I²C 位址

在 PowerShell 執行：

```powershell
python -m mpremote connect COM4 exec "from machine import Pin,I2C; print(I2C(0,sda=Pin(21),scl=Pin(22),freq=400000).scan())"
```

常見結果：

```text
[60]
```

`60` 是十進位，代表 OLED 位址為 `0x3C`。

## 4. 確認驅動程式匹配

確認 `ssd1306.py` 的初始化設定符合實際解析度：

```python
0x12 if self.width == 128 and self.height == 64 else 0x02
```

若驅動程式與 OLED 不匹配，可能出現：

- 文字上下分裂
- 畫面區域錯位
- 像素位置不正確
- 顯示內容被切成兩半

## 5. 執行像素定位測試

定位測試應顯示：

```text
左上角：(0,0)
右上角：(127,0)
左下角：(0,63)
右下角：(127,63)
```

同時測試：

- 中央垂直線
- 最底部水平線
- 中央文字
- 四個角落標記

## 6. 確認座標方向

OLED 座標原點在左上角：

```text
X：由左往右增加，範圍 0～127
Y：由上往下增加，範圍 0～63
```

## 7. 確認後再加入遊戲

定位測試完全正常後，再依序加入：

1. 地板
2. 玩家角色
3. 按鈕輸入
4. 障礙物
5. 碰撞判定
6. 分數與遊戲結束畫面

## 8. 本專案驗證結果

- OLED 解析度：`128x64`
- I²C 位址：`0x3C`
- SDA：`GPIO21`
- SCL：`GPIO22`
- ESP32 序列埠：`COM4`
- 修正驅動初始化後，定位測試與小恐龍遊戲皆正常
