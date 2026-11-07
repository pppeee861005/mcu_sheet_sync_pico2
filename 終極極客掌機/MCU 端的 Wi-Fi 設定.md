# MCU 端 Wi-Fi 設定與連線範本

本文件彙整目前專案常用的 Wi-Fi 連線設定與 MicroPython 連網範本，供 `mcu_sheet_sync`、`農夫機器人` 及其他 IoT 模組參考使用。

---

## 1. 常用 Wi-Fi 熱點資訊

### 方案 A：家用 Wi-Fi (Home Wi-Fi)
- **SSID**：`egg5630`
- **Password**：`27985630`
- **備註**：訊號穩定，適合固定式感測節點。

### 方案 B：手機熱點 (Mobile Hotspot)
- **SSID**：`Redmi 13C`
- **Password**：`chdmchkcrdfd7e8`
- **備註**：適合戶外測試或現場展示使用。

---

## 2. MicroPython 標準連線腳本範本

可直接用於 `boot.py` 或 `main.py` 開頭：

```python
import network
import time

# 選擇要連線的 Wi-Fi（依使用環境切換）
SSID = "egg5630"
PASSWORD = "27985630"

# 或者使用手機熱點：
# SSID = "Redmi 13C"
# PASSWORD = "chdmchkcrdfd7e8"

def connect_wifi(ssid=SSID, password=PASSWORD, timeout_sec=20):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print(f"正在連線至 Wi-Fi: {ssid} ...")
        wlan.connect(ssid, password)
        
        start_time = time.time()
        while not wlan.isconnected():
            if time.time() - start_time > timeout_sec:
                print("\n❌ Wi-Fi 連線逾時，請檢查帳號密碼或熱點狀態！")
                return False
            print(".", end="")
            time.sleep(0.5)
            
    print("\n✅ Wi-Fi 連線成功！")
    ip_info = wlan.ifconfig()
    print("IP 位址 :", ip_info[0])
    print("子網路遮罩 :", ip_info[1])
    print("預設閘道 :", ip_info[2])
    print("DNS 伺服器 :", ip_info[3])
    return True

if __name__ == '__main__':
    connect_wifi()
```

---

## 3. 注意事項

1. **頻段限制**：ESP32 與 Raspberry Pi Pico W 僅支援 **2.4GHz** Wi-Fi 頻段，若手機熱點或家用路由器開了 5GHz，請確認已啟用 2.4GHz 相容模式。
2. **安全性**：包含 Wi-Fi 密碼的程式碼若要開源或推送至 Git，請勿將私人連線金鑰直接 commit 至公開 Repository。
