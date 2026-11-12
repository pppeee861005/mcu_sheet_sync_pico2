# 極客創客避坑寶典：MCU 物聯網開發兩大痛點實戰指南

> **「在單片機與物聯網（IoT）的真實世界裡，魔鬼永遠藏在底層細節中。唯有將血淚經驗化為系統性指南，才能徹底告別重複卡關。」**

本手冊由實戰經驗淬鍊而成，完整收錄在 ESP32 / RP2040 / MicroPython 開發掌機與雲端打卡機時，**最具殺傷力、最容易讓人通宵排錯的兩大核心死穴**與終極標準解法。

---

## 專題一：Google Apps Script (GAS) HTTP 302 重導向與 `EBUSY` 崩潰

### 1. 痛點情境重現
- **現象**：單片機簽到第 1 個人時一切正常，試算表也有新增資料；但**到了第 2 個人，螢幕直接卡死凍結**，或者連線無窮等待。
- **底層報錯**：`OSError: 16 (EBUSY - Device or resource busy)`。

### 2. 踩坑根本原因
1. **Google 的 302 安全重導向機制**：
   - 請求 `script.google.com` 時，Google 為了負載平衡與沙盒執行，一定會回傳 `HTTP 302 Found`，並在 Header 附帶 `Location: https://script.googleusercontent.com/...` 要求客戶端跳轉。
2. **官方 `urequests` 的致命缺陷**：
   - 內建的 `urequests.get()` 雖然會自動追蹤重導向，但它在開啟第二個 Socket 前，**沒有妥善關閉並釋放第一個連線的 TLS/SSL 控制代碼（Handle）**！
   - 單片機（如 ESP32）的 mbedTLS 硬體加速與 RAM 能容納的連線數極為嚴苛。到了第 2 次請求時，底層資源被佔滿，直接拋出 `EBUSY` 崩潰。

### 3. 終極解決方案：原生 SSL Socket 強健客戶端
捨棄 `urequests`，改用自主掌控連線生命週期的標準函式：
- **前置清理**：呼叫 `gc.collect()` 整理記憶體堆疊。
- **超時保護**：設定 `s.settimeout(15.0)`。
- **連線宣告**：HTTP 請求明確宣告 `Connection: close`。
- **讀完立即關閉**：資料讀取完畢後，**先執行 `s.close()` 釋放控制代碼，再進行 302 遞迴跳轉**！

```python
import socket, ssl, json, gc, time

def fetch_gas_request(url):
    gc.collect()
    time.sleep(0.15)
    proto, dummy, host, path = url.split('/', 3)
    port = 443
    ai = socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM)
    addr = ai[0][-1]

    s = socket.socket()
    s.settimeout(15.0)
    try:
        s.connect(addr)
        s = ssl.wrap_socket(s, server_hostname=host)
        req = f"GET /{path} HTTP/1.0\r\nHost: {host}\r\nUser-Agent: ESP32\r\nConnection: close\r\n\r\n"
        s.write(req.encode())

        response = b""
        while True:
            chunk = s.read(512)
            if not chunk:
                break
            response += chunk

        # ★關鍵核心★ 讀完立刻關閉 Socket，絕不殘留！
        s.close()
        gc.collect()

        lines = response.split(b"\r\n")
        status_line = lines[0].decode()
        if "302" in status_line:
            for line in lines:
                if line.lower().startswith(b"location:"):
                    new_url = line.split(b":", 1)[1].strip().decode()
                    return fetch_gas_request(new_url)

        body = response.split(b"\r\n\r\n", 1)[1]
        return json.loads(body.decode())
    except Exception as e:
        try:
            s.close()
        except Exception:
            pass
        gc.collect()
        raise e
```

---

## 專題二：SSD1306 0.96 吋 OLED 繁體中文字模渲染指南

### 1. 痛點情境重現
- **現象**：MicroPython 內建的 `oled.text()` 只能印英文 ASCII，傳入中文直接拋錯。
- **常見失誤**：從網路上隨便找字模工具取模，結果螢幕上的中文字**上下撕裂、左右鏡像顛倒、字形扭曲破碎成亂碼點陣**。

### 2. 踩坑根本原因
點陣顯示的兩個絕對維度必須 100% 吻合：
1. **取模方向錯位（Row-Major 逐行 vs Column-Major 逐列）**：
   - 16x16 點陣由上到下共有 16 列（Row），每列 16 點（2 Bytes：左8點 + 右8點），單字共 32 Bytes。若解算迴圈方向寫反，整行文字會被切成橫向撕裂碎片。
2. **位元映射順序（MSB-First 最高位在前 vs LSB-First 最低位在前）**：
   - 最高位 `bit 7` 必須代表最左邊像素，若顛倒為 `bit 0`，文字會整面水平翻轉（變成鏡像字）。

### 3. 終極解決方案：Python PC 端字型自動光柵化工作流
不要再用老舊的綠色取模工具！直接在電腦端用 Python + Pillow 調用系統微軟正黑體自動產出點陣庫：

#### (1) 自動產生器（PC 端 `generate_fonts.py`）
```python
from PIL import Image, ImageDraw, ImageFont

font = ImageFont.truetype('C:\\Windows\\Fonts\\msjh.ttc', 14)

def glyph_to_bytes(char):
    img = Image.new('1', (16, 16), 0)
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), char, font=font)
    ox = max(0, (16 - (bbox[2] - bbox[0])) // 2) - bbox[0]
    oy = max(0, (16 - (bbox[3] - bbox[1])) // 2) - bbox[1]
    draw.text((ox, oy), char, font=font, fill=1)

    # 標準 Row-Major (MSB First)
    data = []
    for y in range(16):
        b1 = sum((1 << (7 - x)) for x in range(8) if img.getpixel((x, y)))
        b2 = sum((1 << (15 - x)) for x in range(8, 16) if img.getpixel((x, y)))
        data.extend([b1, b2])
    return bytes(data)
```

#### (2) 單片機渲染引擎（MCU 端 `fonts_cn.py`）
```python
def draw_char_16x16(oled, char, x, y, color=1):
    glyph = FONT_16x16.get(char)
    if not glyph:
        oled.rect(x, y, 16, 16, color)  # 缺字方框替代
        return
    for row in range(16):
        b1, b2 = glyph[row * 2], glyph[row * 2 + 1]
        for col in range(8):
            if (b1 >> (7 - col)) & 1:
                oled.pixel(x + col, y + row, color)
            if (b2 >> (7 - col)) & 1:
                oled.pixel(x + 8 + col, y + row, color)
```

---

## 避坑心法總結：創客不卡關的三大鐵律

1. **網路連線先關後開**：
   ESP32 開機或換 Wi-Fi 時，永遠先執行 `wlan.disconnect()` 與短暫 `active(False) -> active(True)`，防止底層 Wi-Fi 棧狀態鎖死。
2. **Socket 生命週期嚴格閉環**：
   單片機沒有虛擬記憶體可用，任何網路請求在處理重導向（302）或拋出異常時，**都必須保證 `s.close()` 並觸發 `gc.collect()`**。
3. **字模格式規格化**：
   點陣字庫永遠嚴格鎖定「16x16 Row-Major, MSB-First」，中英文混排時漢字跨距 `+16`、ASCII 跨距 `+8`，版面永不跑位。
