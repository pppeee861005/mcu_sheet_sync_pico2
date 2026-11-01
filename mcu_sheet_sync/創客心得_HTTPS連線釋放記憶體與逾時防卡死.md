# 創客實戰心得：ESP32 聯網死當避坑秘笈 —— HTTPS 記憶體主動釋放與 5 秒逾時保護

> **日期**：2026-11-01  
> **硬體主控**：ESP32-S3 DevKitC-1  
> **執行環境**：MicroPython v1.2x  
> **核心主題**：HTTPS 連線死當排查、主動記憶體回收 (`gc.collect`)、Socket 逾時保護 (`timeout`)

---

## 💡 一句話總結心得

> **「在每次發起 HTTPS 連線前後主動釋放記憶體；網路請求嚴格限制最長 5 秒，超時拋錯不卡死！」**

在微控制器 (MCU) 開發中，聯網功能（尤其是對 Google Apps Script 的 HTTPS 請求）最常出現的噩夢就是：**「跑一跑突然畫面凍死、按鍵完全沒反應」**。  
過去常以為是多系統負載太重或 CPU 算力不足，但深入底層排查才發現：**MCU 死當絕大多數不是架構太多，而是「無上限的網路阻塞」與「TLS 握手時的記憶體碎片 (Heap Fragmentation)」在作怪！**

---

## 🔍 死當背後的兩大元兇

### 1. 致命的阻塞（Blocking Socket without Timeout）
* **現象**：進入 SkySync 或 Cloud Msg 時，畫面停在載入中，按左鍵或右鍵硬體毫無反應，猶如死機。
* **原因**：MicroPython 內建的 `urequests.get()` 預設沒有設置 `timeout`。當連線到 Google Apps Script 時，需要經過 TLS 握手與一次 302 重新導向。一旦遇上 Wi-Fi 訊號不穩、封包遺失或伺服器延遲，底層 Socket 就會進入**無期限等待 (Infinite Blocking)**，導致整個 MCU 單執行緒迴圈完全凍結！

### 2. TLS 握手的「連續記憶體吞噬」與記憶體碎片
* **現象**：剛開機第一次連線正常，按了幾次或切換畫面後就重啟或當死。
* **原因**：每次建立 HTTPS 連線，ESP32 底層的 `mbedTLS` 加密庫都需要連續的 16KB~30KB 記憶體來配置對稱金鑰與緩衝區。MicroPython 的記憶體回收機制是非壓縮型（Non-compacting），若沒有在連線前整理記憶體，只要 Heap 出現破碎，TLS 握手就會因為找不到「連續區塊」而崩潰。連線完若沒有及時清理，廢棄的物件與 Socket 又會進一步加劇下一輪的破碎。

---

## 🛠️ 最佳實戰解法：穩健的 `safe_gas_get` 封裝

為了解決上述致命傷，我們打造了標準防卡死模式：

```python
import gc
import urequests
import network

def safe_gas_get(params="", timeout=5):
    """
    極客標準防禦模式：
    1. 前後主動 gc.collect()：保持連續記憶體平整
    2. 嚴格限制 timeout=5 秒：逾時主動拋錯，永不凍結
    3. finally 必定關閉 socket：杜絕連線洩漏
    """
    # [步驟 1] 連線前主動釋放記憶體，為 TLS 握手準備平整的連續空間
    gc.collect()
    url = f"{GAS_URL}?{params}" if params else GAS_URL
    r = None
    
    try:
        wlan = network.WLAN(network.STA_IF)
        if not wlan.isconnected():
            return None, "Offline"
            
        # [步驟 2] 限制最長 5 秒超時，超時立即拋出異常，絕不阻塞主迴圈
        r = urequests.get(url, timeout=timeout)
        
        if r.status_code == 200:
            try:
                data = r.json()
                return data, "OK"
            except:
                return r.text, "OK"
        return None, f"HTTP {r.status_code}"
        
    except Exception as e:
        print("連線異常或超時:", e)
        return None, "Timeout/Err"
        
    finally:
        # [步驟 3] 無論成功或拋錯，強制關閉 socket 避免殘留
        if r:
            try:
                r.close()
            except:
                pass
        # [步驟 4] 連線後再次清理，迅速回收 TLS 產生的巨量臨時物件
        gc.collect()
```

---

## 🌟 創客修煉體悟

1. **「寧可報錯顯示 Offline，也絕不讓裝置當機」**：  
   嵌入式系統的精髓在於高可用性與容錯。聯網失敗是常態，只要設定了 5 秒逾時保護，即便在地下室或無網路環境，螢幕也只是彈出 `Offline` 或 `Sync Error`，按鍵依然流暢響應，使用者隨時能繼續操作或手動重試。

2. **主動垃圾回收 (`gc.collect()`) 是 MicroPython 聯網的保命符**：  
   不要等待 MicroPython 記憶體耗盡才自動觸發 GC。在每次發起耗資源的 HTTPS 請求前後，手動呼叫 `gc.collect()`，就像出門前把桌子收拾乾淨、回家後把垃圾倒掉一樣，永遠讓 MCU 保持在最佳餘裕狀態。

3. **系統數量不是瓶頸，健壯的連線保護才是關鍵**：  
   原本懷疑 4 系統負載過重，經過本次實戰證明：4 個系統代碼只佔 28KB，硬體游刃有餘；真正讓 MCU 脫胎換骨的，是這短短幾行「主動釋放」與「超時防護」的工程智慧！
