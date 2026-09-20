# Pico 小恐龍 Dino Game v0.1 開發計劃

## 一、專案目標

使用 Raspberry Pi Pico 2 W + MicroPython，開發第一版「Pico 小恐龍 Dino Game」。

v0.1 不追求完整遊戲，先完成最核心的遊戲機制：

> **恐龍 + 地面 + Button + 跳躍**

完成後，玩家按下 Button，OLED 上的小恐龍會跳起來，再自然落回地面。

---

## 二、v0.1 硬體

### MCU
- Raspberry Pi Pico 2 W
- MicroPython

### Display
- GME12864-11 / SSD1306 OLED
- 128 × 64
- I²C

### Button
- 一顆 Button
- 用來控制「跳躍」

### OLED 接線

目前課程使用的接法：

| OLED | Pico 2 W |
|---|---|
| SDA | GP4 |
| SCL | GP5 |
| VCC | 3V3 |
| GND | GND |

---

## 三、v0.1 遊戲畫面

```text
┌──────────────────────────────┐
│                              │
│        🦖                    │
│                              │
│                              │
│                              │
│______________________________│
└──────────────────────────────┘
```

### 遊戲元素

1. 小恐龍
2. 地面
3. Button
4. 跳躍動畫

---

## 四、v0.1 核心玩法

### 初始狀態

```text
恐龍
 ↓
站在地面
```

### 玩家操作

```text
按 Button
    ↓
恐龍跳躍
    ↓
上升
    ↓
最高點
    ↓
下降
    ↓
回到地面
```

---

## 五、程式設計概念

v0.1 主要練習：

- `Pin`
- Button / Digital Input
- OLED / SSD1306
- `while` 遊戲主迴圈
- 座標 `x / y`
- `if`
- 簡單的跳躍狀態
- `sleep` / 時間控制
- 畫面更新

---

## 六、恐龍資料

先不要使用複雜圖片。

使用簡單的像素圖或矩形表示恐龍。

例如：

```text
  ██
 ████
██████
  ██
 ███
█  █
```

第一階段重點不是美術，而是讓「遊戲物件」動起來。

---

## 七、跳躍邏輯

建立恐龍的基本狀態：

```text
dino_y
velocity_y
```

按下 Button：

```text
velocity_y = -跳躍力量
```

遊戲迴圈：

```text
dino_y = dino_y + velocity_y
velocity_y = velocity_y + gravity
```

當恐龍碰到地面：

```text
dino_y = ground_y
velocity_y = 0
```

這會第一次讓我們接觸真正的「遊戲物理」。

---

## 八、v0.1 開發順序

### Step 1：確認 OLED

先讓 OLED 成功顯示：

```text
PICO DINO
```

### Step 2：畫出地面

```text
________________________
```

### Step 3：畫出恐龍

讓恐龍固定站在地面。

### Step 4：加入 Button

按 Button 時，在 REPL 或畫面上確認：

```text
JUMP!
```

### Step 5：加入跳躍

讓恐龍：

```text
地面
 ↓
上升
 ↓
最高點
 ↓
下降
 ↓
地面
```

### Step 6：加入遊戲主迴圈

整合：

```text
Input
  ↓
Game Logic
  ↓
Physics
  ↓
Display
```

---

## 九、v0.1 完成條件

以下全部成功，才算 v0.1 完成：

- [ ] Pico 2 W 正常執行 MicroPython
- [ ] OLED 正常顯示
- [ ] Button 可以讀取
- [ ] 畫面有地面
- [ ] 畫面有小恐龍
- [ ] 按 Button 可以跳
- [ ] 恐龍會上升
- [ ] 恐龍會下降
- [ ] 恐龍會回到地面
- [ ] 可以連續玩

---

## 十、v0.1 暫時不做

為了控制學習難度，第一版暫時不加入：

- ❌ 仙人掌
- ❌ 障礙物
- ❌ 碰撞判定
- ❌ 分數
- ❌ Game Over
- ❌ 音效
- ❌ Wi-Fi
- ❌ AI

這些留給後面的版本。

---

## 十一、後續版本路線

```text
v0.1
恐龍 + 地面 + 跳躍
        ↓
v0.2
加入仙人掌
        ↓
v0.3
碰撞判定
        ↓
v0.4
分數系統
        ↓
v0.5
速度逐漸增加
        ↓
v1.0
完整 Pico Dino Game
```

---

## 十二、學習目標

這個作品不是單純做一個遊戲。

我們要藉由 Dino Game 把前面學過的能力串起來：

```text
Button
  ↓
GPIO
  ↓
Python
  ↓
Game Logic
  ↓
Physics
  ↓
OLED
  ↓
Game
```

最終目標：

> **讓 Pico 不只是控制 LED，而是能執行一個真正的互動式遊戲。**

---

## 十三、下一刀

### 🎮 下一刀：Step 1

先不做跳躍。

只完成：

> **Pico 2 W → OLED → 顯示一隻小恐龍 + 地面**

完成後，再加入 Button。

