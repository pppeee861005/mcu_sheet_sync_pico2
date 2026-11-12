#########################################################################
# Python x AI Agent
# Json, API, CLI - 應用程式介面、命令列參數
#
# [專案]
# 證券分析爬蟲
#
# 問題：請詳閱附件 ReadMe_stocks.pdf
#       撰寫程式上網爬取大盤、個股基本面、近期股價資訊，
#       藉以針對某支股票給出客觀的趨勢分析。
#
# 輸入：台灣證券交易所 (TWSE) 所提供的資料、
#       股票代碼
#
# 輸出：
#     命令列指定選項，使用 tabulate 模組印出文字表格：
#     1)-i 選項：近期大盤資訊
#     2)-p 股票代碼：個股的近期股價資料
#     3)-v 股票代碼：個股日殖利率、本益比及股價淨值比
#
##########################################################################

import argparse
import datetime
import time
import requests
from tabulate import tabulate

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def get_prev_month(year: int, month: int):
    """計算前一個月的年份與月份"""
    if month == 1:
        return year - 1, 12
    return year, month - 1

# 抓取大盤指數
def index_info(data_num: int=10) -> str:
    """
    依照指定的資料筆數，從證交所網站抓取大盤指數的資料

    Parameters:
        data_num : (int, optional)
            希望顯示的資料日期數, 預設為 10

    Returns:
        (str)
        轉換成文字表格的資料
    """
    url_template = 'https://www.twse.com.tw/rwd/zh/afterTrading/FMTQIK?date={date_string}&response=json'
    now = datetime.date.today()
    curr_year, curr_month = now.year, now.month

    collected_data = []
    fields = ['日期', '成交股數', '成交金額', '成交筆數', '發行量加權股價指數', '漲跌點數']

    # 最多往前查詢 12 個月
    for _ in range(12):
        date_str = f"{curr_year}{curr_month:02d}01"
        try:
            resp = requests.get(url_template.format(date_string=date_str), headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                res_json = resp.json()
                if res_json.get('stat') == 'OK' and 'data' in res_json:
                    if 'fields' in res_json:
                        fields = res_json['fields']
                    # 月份內的資料按日期升冪，向前疊加
                    month_data = res_json['data']
                    collected_data = month_data + collected_data
                    if len(collected_data) >= data_num:
                        break
        except Exception:
            pass

        curr_year, curr_month = get_prev_month(curr_year, curr_month)
        time.sleep(0.5)

    if not collected_data:
        return "查無大盤資訊或無法連線至證交所。"

    result_data = collected_data[-data_num:]
    return tabulate(result_data, headers=fields, tablefmt='pretty')


# 抓取股價資料
def stock_price(stock_index: str, data_num: int=10) -> str:
    """
    依照指定的資料筆數，從證交所網站抓取個別股票過去一段時間內的股價資料

    Parameters:
        stock_index : (required)
            股票代號
        data_num :
            希望顯示的資料日期數, 預設為 10

    Returns:
        (str)
        轉換成文字表格的資料
    """
    url_template = 'https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY?date={date_string}&stockNo={stock_index}&response=json'
    now = datetime.date.today()
    curr_year, curr_month = now.year, now.month

    collected_data = []
    fields = []

    for _ in range(12):
        date_str = f"{curr_year}{curr_month:02d}01"
        try:
            url = url_template.format(date_string=date_str, stock_index=stock_index)
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                res_json = resp.json()
                if res_json.get('stat') == 'OK' and 'data' in res_json:
                    if 'fields' in res_json and not fields:
                        fields = res_json['fields']
                        month_data = res_json['data']
                        collected_data = month_data + collected_data
                        if len(collected_data) >= data_num:
                            break
        except Exception:
            pass

        curr_year, curr_month = get_prev_month(curr_year, curr_month)
        time.sleep(0.5)

    if not collected_data:
        return f"查無股票代號 {stock_index} 之股價資料或無法連線至證交所。"

    result_data = collected_data[-data_num:]
    return tabulate(result_data, headers=fields, tablefmt='pretty')


# 抓取基本面資料
def stock_value(stock_index: str, data_num: int=10) -> str:
    """
    依照指定的資料筆數，從證交所網站抓取個別股票過去一段時間內的基本面資料，
    包含個股日殖利率、本益比及股價淨值比

    Parameters:
        stock_index : (required)
            股票代號
        data_num :
            希望顯示的資料日期數, 預設為 10

    Returns:
        (str)
        轉換成文字表格的資料
    """
    url_template = 'https://www.twse.com.tw/rwd/zh/afterTrading/BWIBBU?date={date_string}&stockNo={stock_index}&response=json'
    now = datetime.date.today()
    curr_year, curr_month = now.year, now.month

    collected_data = []
    fields = []

    for _ in range(12):
        date_str = f"{curr_year}{curr_month:02d}01"
        try:
            url = url_template.format(date_string=date_str, stock_index=stock_index)
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                res_json = resp.json()
                if res_json.get('stat') == 'OK' and 'data' in res_json:
                    if 'fields' in res_json and not fields:
                        fields = res_json['fields']
                    month_data = res_json['data']
                    collected_data = month_data + collected_data
                    if len(collected_data) >= data_num:
                        break
        except Exception:
            pass

        curr_year, curr_month = get_prev_month(curr_year, curr_month)
        time.sleep(0.5)

    if not collected_data:
        return f"查無股票代號 {stock_index} 之基本面資料或無法連線至證交所。"

    result_data = collected_data[-data_num:]
    return tabulate(result_data, headers=fields, tablefmt='pretty')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', action='store_true', help='近期大盤資訊')
    parser.add_argument('-p', '--price', help='個股的近期股價資料')
    parser.add_argument('-v', '--value', help='個股日殖利率、本益比及股價淨值比')
    args = parser.parse_args()

    if args.i:
        print('\n大盤指數資訊：\n')
        print(index_info())
    if args.price:
        print(f'\n{args.price} 各日成交資訊：\n')
        print(stock_price(args.price))
    if args.value:
        print(f'\n{args.value} 個股日殖利率、本益比及股價淨值比：\n')
        print(stock_value(args.value))

    print()

if __name__ == '__main__':
    main()
