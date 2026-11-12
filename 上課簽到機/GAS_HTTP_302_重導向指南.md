# Google Apps Script (GAS) HTTP 302 重導向與單片機 (MCU) 踩坑防禦指南

本指南深入剖析在物聯網（IoT / MicroPython / ESP32 / RP2040）開發中，將 Google Apps Script (GAS) 作為免費雲端資料庫/中繼 API 時，**最容易引發崩潰、記憶體洩漏與「簽到一次就卡死」的終極元凶——HTTP 302 重導向（Redirect）**，並提供最健壯的底層解決方案。

---

## 1. 什麼是 Google Apps Script 的 302 重導向機制？

當我們將 GAS 專案部署為「網路應用程式 (Web App)」時，會獲得類似下方的端點網址：
```text
https://script.google.com/macros/s/{SCRIPT_ID}/exec?name=...
```

### Google 內部的工作流程：
1. **第一次請求**：單片機發送 HTTP GET 請求到 `script.google.com`。
2. **負載平衡與安全隔離**：Google 伺服器**不會**直接在該網址回傳您的 JSON 資料。為了安全隔離與沙盒執行，Google 會回傳 **`HTTP/1.0 302 Moved Temporarily`** 或 **`302 Found`**。
3. **Location 標頭**：在 Response Header 中，Google 會給出一個極長的暫時執行網址：
   ```text
   Location: https://script.googleusercontent.com/macros/echo?user_content_key=...
   ```
4. **第二次請求**：客戶端必須向 `script.googleusercontent.com` 發起第二次請求，才能真正拿到腳本輸出的 JSON 結果。

---

## 2. 為什麼 MicroPython 內建的 `urequests` 會害單片機卡死？

MicroPython 官方精簡庫 `urequests.py` 雖然具備簡易的 302 重導向追蹤，但在 ESP32 / RP2040 這種資源受限的硬體上存在兩大致命缺陷：

### 致命傷一：Socket 與 SSL 資源洩漏 (Resource Leak)
- 當 `urequests.get()` 收到 302 時，它會遞迴呼叫自己去抓取新的 `Location` 網址。
- 然而，**第一個連接至 `script.google.com` 的 TLS/SSL Socket 往往沒有被明確執行 `.close()`**。
- ESP32 的底層 mbedTLS / LwIP 堆疊能同時維持的 SSL 連線數極為有限（通常僅 1~2 個）。

### 致命傷二：錯誤代碼 `OSError: 16 (EBUSY)`
- 當學生打卡第一次成功後，第二位同學打卡時，底層發現上一個 SSL 連線控制代碼（Handle）尚未釋放。
- 此時 `s.connect()` 或 `ssl.wrap_socket()` 會直接拋出 **`OSError: 16 (EBUSY - Device or resource busy)`**。
- 單片機因此陷入無窮等待、死鎖或畫面凍結，造成「資料有寫入試算表，但螢幕直接卡死」的詭異現象。

---

## 3. 終極解決方案：原生 SSL Socket 強健客戶端

要徹底杜絕 `EBUSY` 與 302 重導向卡死，必須**捨棄依賴 `urequests`**，改用明確掌控生命週期的底層 `socket` + `ssl` 實作：

### 核心演算法架構：
```text
[開始請求]
   │
   ├── 1. gc.collect() 主動清理釋放 RAM
   ├── 2. 建立 Socket 並包裝 TLS/SSL (ssl.wrap_socket)
   ├── 3. 發送 HTTP/1.0 GET (宣告 Connection: close)
   ├── 4. 讀取完整回應並提取 Header
   ├── 5. 立即執行 s.close() 關閉連線 (關閉連線優先！)
   │
[判斷狀態碼]
   │
   ├── 若包含 "302" -> 取得 Location 標頭，進行乾淨的二次遞迴
   └── 若為 "200"   -> 解析 Body JSON，返回乾淨數據
```

---

## 4. 完整 Python 實作程式碼 (可直接複製使用)

此函式可直接取代 `urequests.get()`，完全免疫連線殘留與記憶體溢出：

```python
import socket
import ssl
import json
import gc
import time

def fetch_gas_request(url):
    """
    專為 Google Apps Script 打造的強健型 HTTPS 客戶端
    1. 完美處理 302 重導向
    2. 保證嚴格執行 Socket.close() 與 gc.collect()
    3. 徹底免疫 OSError: 16 (EBUSY)
    """
    # 步驟 1: 前置回收記憶體並微幅延遲確保硬體穩定
    gc.collect()
    time.sleep(0.15)

    # 步驟 2: 解析網址與主機
    proto, dummy, host, path = url.split('/', 3)
    port = 443
    ai = socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM)
    addr = ai[0][-1]

    s = socket.socket()
    s.settimeout(15.0)  # 設定 15 秒安全連線逾時

    try:
        # 步驟 3: 握手建立安全 TLS 連線
        s.connect(addr)
        s = ssl.wrap_socket(s, server_hostname=host)
        
        # 宣告 Connection: close，通知 Google 傳送完即斷開
        req = f"GET /{path} HTTP/1.0\r\nHost: {host}\r\nUser-Agent: MicroPython-IoT\r\nConnection: close\r\n\r\n"
        s.write(req.encode())

        # 步驟 4: 讀取回應封包
        response = b""
        while True:
            chunk = s.read(512)
            if not chunk:
                break
            response += chunk

        # 步驟 5: ★關鍵核心★ 資料讀完立刻關閉 Socket，絕不佔用控制代碼！
        s.close()
        gc.collect()

        # 步驟 6: 判斷 302 重導向
        lines = response.split(b"\r\n")
        status_line = lines[0].decode()

        if "302" in status_line:
            # 尋找 Location 標頭
            for line in lines:
                if line.lower().startswith(b"location:"):
                    new_url = line.split(b":", 1)[1].strip().decode()
                    # 乾淨安全地發起第二次跳轉請求
                    return fetch_gas_request(new_url)

        # 步驟 7: 提取並解析 JSON 資料
        body = response.split(b"\r\n\r\n", 1)[1]
        return json.loads(body.decode())

    except Exception as e:
        # 任何異常發生時，務必確保 Socket 關閉
        try:
            s.close()
        except Exception:
            pass
        gc.collect()
        raise e
```

---

## 5. GAS 端的最佳化建議 (`google_apps_script.js`)

在 Google Apps Script 端，為了讓單片機最快拿到回應、縮短連線時間，建議：

1. **一律使用 `ContentService.createTextOutput()` 並指定 JSON**：
   ```javascript
   return ContentService.createTextOutput(JSON.stringify(result))
          .setMimeType(ContentService.MimeType.JSON);
   ```
2. **避免回傳 HTML 網頁**：不要使用 `HtmlService.createHtmlOutput()`，因為 HTML 標籤體積大，會增加單片機的字串處理負擔與記憶體消耗。
3. **控制資料大小**：只回傳必要的欄位（如 `status`、`name`、`time`），讓單片機可以在 1~2 個 512 bytes 的 buffer 內就接收完畢。

---

## 6. 避障排錯對照表 (Troubleshooting)

| 異常現象 / 錯誤訊息 | 原因 | 處理解法 |
| :--- | :--- | :--- |
| **`OSError: 16 (EBUSY)`** | 上一次 SSL Socket 尚未 close() 即開新連線 | 改用本指南之 `fetch_gas_request`，保證關閉連線。 |
| **`HTTP Error 403 Forbidden`** | GAS 部署權限未開放給「所有人」 | 管理部署作業 $\rightarrow$ 誰可以存取改為 **「所有人 (Anyone)」**。 |
| **試算表有新增資料，但單片機報錯** | 寫入成功，但讀取 302 跳轉網址時逾時或斷線 | 確保 `s.settimeout(15.0)` 給予足夠時間接收跳轉封包。 |
| **`MemoryError` 記憶體溢出** | 讀取重導向大封包時 RAM 耗盡 | 每次呼叫前後務必加入 `gc.collect()` 整理堆疊記憶體。 |
