"""
Google Sheets 存取與操作範例 (OAuth 服務帳號)
來源改寫自：`「豪力的api_ipynb」的副本.ipynb` -> Oauth - 存取 Google 試算表
"""

from pathlib import Path
import gspread
from oauth2client.service_account import ServiceAccountCredentials as sac

# 1. 設定工作路徑與認證金鑰檔案
# 預設抓取目前腳本所在目錄下的 google_auth.json
CURRENT_DIR = Path(__file__).resolve().parent
oauth_file = CURRENT_DIR / 'google_auth.json'

# Google Sheets API 權限範圍 (Scope)
scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]

def main():
    if not oauth_file.exists():
        print(f"⚠️ 找不到金鑰檔案：{oauth_file}")
        print("請確認已將 Google Cloud 服務帳號金鑰 (JSON 格式) 放置於本目錄，並命名為 google_auth.json")
        return

    # 2. 建立憑證並授權
    print("正在建立憑證並連線到 Google Sheets...")
    cr = sac.from_json_keyfile_name(str(oauth_file), scope)
    gs = gspread.authorize(cr)

    # 3. 開啟試算表與工作表
    # 請將「智慧農場試算表」改為您實際在 Google 雲端硬碟建立的試算表名稱
    spreadsheet_name = '智慧農場試算表'
    worksheet_name = '銷售報表'

    print(f"開啟試算表：{spreadsheet_name} -> 工作表：{worksheet_name}")
    sh = gs.open(spreadsheet_name)
    # 也可以透過 sh.sheet1 開啟第一個工作表：
    # wks = sh.sheet1
    wks = sh.worksheet(worksheet_name)

    # 4. 更新儲存格
    print("更新儲存格 C2 與 (列4, 欄3)...")
    wks.update_acell('C2', 'Green Tea')
    wks.update_cell(4, 3, 'Black Tea')  # 第 4 列，第 3 欄儲存格

    # 5. 寫入整列 (在第 1 列插入資料)
    print("在第 1 列插入標題資料...")
    values = ['Name', 'Year', 'Product', 'Price', 'Quantity', 'Revenue', 'Location']
    wks.insert_row(values, 1)

    # 6. 讀取儲存格與內容
    print("\n--- 讀取內容 ---")
    print("A1 儲存格內容 (acell):", wks.acell('A1').value)
    print("第 1 列第 1 欄內容 (cell):", wks.cell(1, 1).value)
    print("第 1 列所有值 (row_values):", wks.row_values(1))
    print("第 1 欄所有值 (col_values):", wks.col_values(1))
    print("整張工作表內容 (get_all_values):", wks.get_all_values())

    # 7. 保留第一列，其餘刪除 (依需求啟用)
    # print("調整工作表大小，僅保留第 1 列...")
    # wks.resize(1)

if __name__ == '__main__':
    main()
