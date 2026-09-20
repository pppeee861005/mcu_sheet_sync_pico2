# OLED 顯示修正報告

## 問題

小恐龍遊戲畫面曾出現以下異常：

- 文字在 OLED 上下分裂顯示。
- `128x64` 文字的上半部與下半部位置錯誤。
- 遊戲座標看起來與實際畫面不一致。

## 確認結果

定位測試確認 OLED 的四個角落、中央垂直線與邊界都能正常顯示，因此：

- ESP32 與 OLED 的 I²C 通訊正常。
- SDA 使用 GPIO21。
- SCL 使用 GPIO22。
- OLED 解析度為 128x64。
- 問題不是恐龍座標或遊戲邏輯。

## 問題原因

`ssd1306.py` 中 128x64 OLED 的 COM 腳位設定寫反：

```python
# 錯誤設定
0x02 if self.width == 128 and self.height == 64 else 0x12
```

這會造成 OLED 的畫面記憶體與實際顯示區域錯位，導致文字上下分裂。

## 修正內容

已修改為：

```python
# 正確設定
0x12 if self.width == 128 and self.height == 64 else 0x02
```

並重新上傳：

```powershell
python -m mpremote connect COM4 fs cp .\ssd1306.py :ssd1306.py
python -m mpremote connect COM4 fs cp .\main.py :main.py
python -m mpremote connect COM4 reset
```

## 目前接線

```text
OLED VCC      -> ESP32 3V3
OLED GND      -> ESP32 GND
OLED SDA      -> GPIO21
OLED SCL/SCK  -> GPIO22
按鈕一腳      -> GPIO18
按鈕另一腳    -> GND
```

## 驗證結果

- OLED 定位測試顯示正確。
- `128x64` 文字完整顯示。
- 橫線位於畫面底部。
- 小恐龍遊戲已恢復正常。
- ESP32 使用 COM4，MicroPython 與 `mpremote` 通訊正常。
