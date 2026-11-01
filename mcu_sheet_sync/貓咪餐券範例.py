# -*- coding: utf-8 -*-
"""
貓咪餐券獨立範例 (Cat Meal Voucher Standalone)
從 SkyDeck OS 系統中獨立提取出來的單機儀式感小遊戲

硬體配置：
  - 主控：ESP32-S3 DevKitC-1
  - 螢幕：0.96" OLED (SSD1306, I2C: SDA=21, SCL=22)
  - 按鈕：
      - 右鍵 (GPIO 4 - 長按蓄力 2 秒撕票 / 核銷餐券)
      - 左鍵 (GPIO 18)

特色：
  1. 完整擬真的打孔虛線餐券票面（MEAL TICKET : 1）。
  2. 長按 2 秒撕票蓄力動畫與進度條反饋。
  3. 動態撕票特效（左右紙片飛散裂開）。
  4. 貓咪驚喜表情包與開心吃大餐動畫（Nyanko Feast）。
  5. 防重複核銷機制（單次開機限兌換一次，需重開機重置）。
"""

import time
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C

# ================= 硬體腳位定義 =================
I2C_SDA_PIN = 21
I2C_SCL_PIN = 22
BUTTON_LEFT_PIN = 18    # 左鍵 (備用)
BUTTON_RIGHT_PIN = 4    # 右鍵 (長按 2 秒核銷餐券)

OLED_WIDTH = 128
OLED_HEIGHT = 64

# ================= 硬體初始化 =================
i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=400000)
oled = SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c)

btn_left = Pin(BUTTON_LEFT_PIN, Pin.IN, Pin.PULL_UP)
btn_right = Pin(BUTTON_RIGHT_PIN, Pin.IN, Pin.PULL_UP)


# ================= 貓咪餐券核心函數 =================
def run_cat_ticket():
    """貓咪餐券核心邏輯"""
    tickets = 1  # 初始擁有一張餐券
    
    def render_voucher_ready():
        """渲染待核銷的餐券票面"""
        oled.fill(0)
        # 標題反白列
        oled.fill_rect(0, 0, 128, 13, 1)
        oled.text("* CAT VOUCHER *", 8, 3, 0)
        
        # 餐券外框與內容
        oled.rect(8, 18, 112, 28, 1)
        oled.text("MEAL TICKET : 1", 12, 23, 1)
        oled.text("Feast For Kitty", 12, 34, 1)
        
        # 繪製票券中間打孔虛線 (Perforated line)
        for x in range(12, 118, 6):
            oled.pixel(x, 29, 0)
            
        # 底部操作提示
        oled.hline(0, 50, 128, 1)
        oled.text("Hold R to TEAR!", 6, 54, 1)
        oled.show()

    def render_sold_out():
        """渲染餐券已使用 (作廢) 畫面"""
        oled.fill(0)
        oled.fill_rect(0, 0, 128, 13, 1)
        oled.text("  TICKET USED   ", 8, 3, 0)
        
        oled.rect(10, 18, 108, 28, 1)
        oled.text("[ VOID / USED ]", 12, 23, 1)
        oled.text("Kitty is full! ", 12, 34, 1)
        
        oled.hline(0, 50, 128, 1)
        oled.text("Reboot to Refill", 4, 54, 1)
        oled.show()

    def play_tear_and_feast():
        """撕票儀式與貓咪享用大餐動畫"""
        # 動畫 1：動態撕票裂開特效（左右兩半分離）
        for shift in range(0, 35, 4):
            oled.fill(0)
            # 左半張票
            oled.rect(8 - shift, 18, 56, 28, 1)
            oled.text("CAT", 14 - shift, 24, 1)
            oled.text("MEAL", 14 - shift, 34, 1)
            
            # 右半張票
            oled.rect(64 + shift, 18, 56, 28, 1)
            oled.text("TICKET", 68 + shift, 24, 1)
            oled.text("VOID", 68 + shift, 34, 1)
            
            oled.text("TEARING TICKET...", 0, 52, 1)
            oled.show()
            time.sleep_ms(35)
            
        # 動畫 2：貓咪登場與狂歡吃大餐
        for _ in range(2):
            # 貓咪好奇
            oled.fill(0)
            oled.text("(=^･ｪ･^=) ?", 24, 20, 1)
            oled.text("Is that for ME?!", 4, 38, 1)
            oled.show()
            time.sleep_ms(300)
            
            # 貓咪開動大嚼
            oled.fill(0)
            oled.text("(=^･ω･^=) NYA!", 16, 20, 1)
            oled.text("FEAST TIME! *Nom*", 2, 38, 1)
            oled.show()
            time.sleep_ms(400)
            
        # 動畫 3：全螢幕白閃慶祝
        for _ in range(3):
            oled.invert(1)
            time.sleep_ms(80)
            oled.invert(0)
            time.sleep_ms(80)

    # 首次啟動繪製餐券
    render_voucher_ready()
    last_r = 1
    
    print(">> 貓咪餐券機啟動完成！請按住右鍵 (GPIO 4) 2 秒進行撕票核銷...")
    
    while True:
        vr = btn_right.value()
        
        # 偵測右鍵按下
        if last_r == 1 and vr == 0:
            time.sleep_ms(30)  # 防彈跳消除
            if btn_right.value() == 0 and tickets > 0:
                press_start = time.time()
                # 進入長按蓄力監聽迴圈
                while btn_right.value() == 0:
                    elapsed = time.time() - press_start
                    pct = min(1.0, elapsed / 2.0)
                    
                    oled.fill(0)
                    oled.fill_rect(0, 0, 128, 13, 1)
                    oled.text("Tearing Ticket..", 4, 3, 0)
                    oled.text(f"Holding... {int(pct*100)}%", 10, 22, 1)
                    
                    # 繪製撕票進度條
                    oled.rect(14, 36, 100, 8, 1)
                    oled.fill_rect(16, 38, int(pct * 96), 4, 1)
                    oled.show()
                    time.sleep_ms(40)
                    
                    # 蓄力達到 2 秒，達成撕票條件！
                    if elapsed >= 2.0:
                        tickets = 0
                        play_tear_and_feast()
                        render_sold_out()
                        while btn_right.value() == 0:
                            time.sleep_ms(30)
                        break
                else:
                    # 中途放開按鍵，取消核銷恢復原狀
                    if tickets > 0:
                        render_voucher_ready()
            elif tickets == 0 and btn_right.value() == 0:
                # 票券已使用完畢之友善提示
                oled.fill(0)
                oled.text("NO TICKETS!", 20, 20, 1)
                oled.text("Please REBOOT", 16, 36, 1)
                oled.show()
                time.sleep(1.2)
                render_sold_out()
                while btn_right.value() == 0:
                    time.sleep_ms(20)
                    
        last_r = vr
        time.sleep_ms(30)


# ================= 程式主入口 =================
if __name__ == "__main__":
    run_cat_ticket()
