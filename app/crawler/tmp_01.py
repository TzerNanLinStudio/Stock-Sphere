import json

import sys
import os

import yfinance as yf
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime


def scrape_sp500_from_snapshot(snapshot_url):
    """從 Wayback Machine 快照抓取 S&P 500 資料"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = requests.get(snapshot_url, headers=headers, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    response = requests.get(snapshot_url, headers=headers)
    print(f"狀態碼: {response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")
    rows = soup.select("table.table tbody tr")
    print(f"找到 {len(rows)} 筆資料")

    data = []
    for idx, row in enumerate(rows[:100]):
        cols = row.find_all("td")

        # Debug: 印出前3筆的所有欄位
        if idx < 3:
            print(f"\n第 {idx+1} 筆資料,共 {len(cols)} 個欄位:")
            for i, col in enumerate(cols):
                print(f"  欄位 {i}: {col.text.strip()}")

        if len(cols) >= 3:  # 確保有足夠的欄位
            rank = cols[0].text.strip()
            symbol = cols[2].text.strip()
            name = cols[1].text.strip()
            data.append([rank, symbol, name])

    df = pd.DataFrame(data, columns=["rank", "symbol", "company"])
    print(df)

    return df

def save_df_to_json(df, folder_path, filename=None):
    """
    將 DataFrame 儲存為 JSON 檔案，檔名格式為：年月日_時分秒.json

    參數：
        df (pd.DataFrame): 要儲存的資料
        folder_path (str): 要儲存的資料夾路徑
        filename (str, optional): 檔案名稱，若為空則使用時間戳命名
    """
    # 確保資料夾存在
    os.makedirs(folder_path, exist_ok=True)

    # 生成檔案名稱
    if filename is None or filename == "":
        filename = datetime.now().strftime("%Y%m%d_%H%M%S.json")
    elif not filename.endswith('.json'):
        filename = f"{filename}.json"

    filepath = os.path.join(folder_path, filename)

    # 儲存為 JSON
    df.to_json(filepath, orient='records', force_ascii=False, indent=2)
    print(f'檔案已儲存至：{filepath}')

def start_point():
    # df = scrape_sp500_from_snapshot("https://web.archive.org/web/20240103123326/https://https://www.slickcharts.com/sp500")
    # save_df_to_json(df[["symbol"]], "document/rank", "top100_2024")

    df = scrape_sp500_from_snapshot("https://www.slickcharts.com/sp500")
    save_df_to_json(df, "document/rank")

