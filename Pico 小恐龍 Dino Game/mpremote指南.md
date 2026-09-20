可以，ESP32 使用 MicroPython 時，建議透過 PowerShell 搭配 mpremote 燒錄程式。

  ## 1. 安裝工具

  在 PowerShell 執行：

  py -m pip install mpremote esptool

  確認安裝成功：

  mpremote version
  esptool version

  ## 2. 找出 ESP32 的 COM 埠

  將 ESP32 接上 USB，執行：

  Get-CimInstance Win32_SerialPort | Select-Object DeviceID,Description

  例如看到：

  COM3  USB-SERIAL CH340

  代表 ESP32 是 COM3。

  ## 3. 第一次使用時燒錄 MicroPython 韌體

  先下載對應 ESP32 型號的 .bin 韌體，例如 ESP32、ESP32-S3、ESP32-C3 必須選正確版本。

  清除 Flash：

  esptool --port COM3 erase-flash

  燒錄韌體：

  esptool --chip esp32 --port COM3 --baud 460800 write-flash -z 0x1000 firmware.bin

  將：

  - COM3 改成你的實際 COM 埠
  - esp32 改成你的晶片型號
  - firmware.bin 改成韌體檔案完整路徑

  例如：

  esptool --chip esp32 --port COM3 --baud 460800 write-flash -z 0x1000 'D:\Downloads\ESP32_GENERIC-20260101-v1.27.0.bin'

  ## 4. 將程式燒錄到 ESP32

  切換到你的專案資料夾：

  Set-Location 'D:\練習操作區\創客\Pico 小恐龍 Dino Game'

  上傳 main.py：

  mpremote connect COM3 fs cp .\main.py :main.py

  上傳 ssd1306.py：

  mpremote connect COM3 fs cp .\ssd1306.py :ssd1306.py

  也可以一次上傳：

  mpremote connect COM3 fs cp .\main.py :main.py .\ssd1306.py :ssd1306.py

  ESP32 重新啟動：

  mpremote connect COM3 reset

  因為檔名是 main.py，ESP32 重開後會自動執行小恐龍遊戲。

  ## 5. 查看錯誤訊息

  若遊戲沒有啟動，可開啟序列埠：

  mpremote connect COM3 repl

  按下 Ctrl+D 重新執行程式；若程式有錯，錯誤訊息會顯示在 PowerShell。

  若出現連線失敗，請確認：

  - COM 埠沒有被 Arduino IDE 或 Thonny 佔用
  - USB 線支援資料傳輸
  - ESP32 使用正確的 MicroPython 韌體
  - 燒錄時必要時按住 ESP32 的 BOOT 鍵再放開



假設 ESP32 的序列埠是 COM3，PowerShell 指令如下：

  mpremote connect COM3 fs cp 'D:\練習操作區\創客\Pico 小恐龍 Dino Game\main.py' :main.py

  你的 main.py 需要 ssd1306.py，建議一起上傳：

  mpremote connect COM3 fs cp 'D:\練習操作區\創客\Pico 小恐龍 Dino Game\main.py' :main.py 'D:\練習操作區\創
  客\Pico 小恐龍 Dino Game\ssd1306.py' :ssd1306.py

  上傳後重新啟動 ESP32：

  mpremote connect COM3 reset

  如果不是 COM3，先查詢：

  Get-CimInstance Win32_SerialPort | Select-Object DeviceID,Description

  把指令中的 COM3 改成實際的 COM 埠即可。