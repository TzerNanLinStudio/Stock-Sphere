import json

import sys
import os

import yfinance as yf
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

def get_sp500_historical_snapshots(years=[2019, 2020, 2021], save_func=None):
    """
    從 Wayback Machine 抓取 Wikipedia S&P 500 歷史版本
    找出每年第一個快照，存成 df 後呼叫 save_func
    
    Parameters:
    -----------
    years : list
        要抓取的年份列表
    save_func : function
        儲存函數，格式為 save_func(df, folder, filename)
    """
    
    for year in years:
        print(f"\n🔍 正在處理 {year} 年...")
        
        # 找出該年第一個可用的快照
        snapshot_url = find_first_snapshot(year)
        
        if snapshot_url is None:
            print(f"❌ 找不到 {year} 年的快照")
            continue
        
        print(f"✅ 找到快照: {snapshot_url}")
        
        # 抓取該快照的資料
        try:
            df = scrape_sp500_from_snapshot(snapshot_url)
            print(f"✅ 成功抓取 {year} 年資料，共 {len(df)} 筆")
            
            # 呼叫儲存函數
            if save_func:
                save_func(df, "document", f"sp500_{year}")
                print(f"✅ 已儲存 {year} 年資料")
            
            # 禮貌性等待
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ 抓取 {year} 年資料時發生錯誤: {e}")


def find_first_snapshot(year):
    """找出指定年份第一個可用的 Wayback Machine 快照"""
    
    # Wayback Machine CDX API
    cdx_api = "http://web.archive.org/cdx/search/cdx"
    
    params = {
        'url': 'en.wikipedia.org/wiki/List_of_S%26P_500_companies',
        'from': f'{year}0101',
        'to': f'{year}1231',
        'output': 'json',
        'limit': '1',
        'filter': 'statuscode:200'
    }
    
    try:
        response = requests.get(cdx_api, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if len(data) > 1:
            timestamp = data[1][1]
            snapshot_url = f"https://web.archive.org/web/{timestamp}/https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            return snapshot_url
            
    except Exception as e:
        print(f"⚠️  API 查詢失敗: {e}")
    
    # 備用方法：嘗試常見日期
    common_dates = [
        f'{year}0101', f'{year}0115', f'{year}0201', 
        f'{year}0301', f'{year}0401', f'{year}0501'
    ]
    
    for date in common_dates:
        test_url = f"https://web.archive.org/web/{date}/https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        try:
            response = requests.head(test_url, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                return test_url
        except:
            continue
    
    return None


def scrape_sp500_from_snapshot(snapshot_url):
    """從 Wayback Machine 快照抓取 S&P 500 資料"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = requests.get(snapshot_url, headers=headers, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # 找到第一個表格
    table = soup.find('table', {'class': 'wikitable sortable'})
    
    if table is None:
        table = soup.find('table', {'id': 'constituents'})
    
    if table is None:
        raise ValueError("找不到 S&P 500 表格")
    
    # 解析表格標題
    headers = []
    header_row = table.find('tr')
    for th in header_row.find_all('th'):
        headers.append(th.get_text(strip=True))
    
    # 讀取資料行
    rows = []
    for tr in table.find_all('tr')[1:]:
        cells = tr.find_all(['td', 'th'])
        if len(cells) > 0:
            row = [cell.get_text(strip=True) for cell in cells]
            rows.append(row)
    
    # 建立 DataFrame
    df = pd.DataFrame(rows, columns=headers)
    
    # 清理資料
    df = df.dropna(how='all')
    df.columns = df.columns.str.strip()
    df = df.reset_index(drop=True)
    
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
    # https://web.archive.org/web/20250415000000*/https://en.wikipedia.org/wiki/List_of_S%26P_500_companies
    get_sp500_historical_snapshots(years=[2014, 2015, 2016, 2017, 2018], save_func=save_df_to_json)

