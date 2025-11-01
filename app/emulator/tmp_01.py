import yfinance as yf
import pandas as pd
import json

top_company_file = "document/rank/top100_2019.json"
top_company_count = 25
start_date = "2019-01-01"
end_date = "2019-12-31"

def get_stock_info(symbol, start_date, end_date):
    """
    獲取股票在指定日期範圍內的歷史資料
    
    參數:
        symbol (str): 股票代碼，例如 "AAPL"
        start_date (str): 起始日期，格式 "YYYY-MM-DD"
        end_date (str): 結束日期，格式 "YYYY-MM-DD"
    
    返回:
        DataFrame: 股票歷史資料
    """
    # 獲取股票資料
    ticker_data = yf.Ticker(symbol)

    # 獲取指定日期範圍的歷史資料
    ticker_df = ticker_data.history(start=start_date, end=end_date)

    # 計算KDJ指標
    low_list = ticker_df['Low'].rolling(9).min()
    high_list = ticker_df['High'].rolling(9).max()
    rsv = (ticker_df['Close'] - low_list) / (high_list - low_list) * 100

    ticker_df['K'] = rsv.ewm(com=2).mean()
    ticker_df['D'] = ticker_df['K'].ewm(com=2).mean()
    ticker_df['J'] = 3 * ticker_df['K'] - 2 * ticker_df['D']

    # 顯示資料
    #print(f"股票代碼: {symbol}")
    #print(f"日期範圍: {start_date} 至 {end_date}")
    #print(f"總共有 {len(ticker_df)} 筆資料\n")
    #print(ticker_df)
    
    return ticker_df

def get_top_company_symbol(path, number):
    """
    從JSON文件讀取前N個公司股票代號

    參數:
        path (str): JSON文件路徑
        number (int): 要取得的股票數量

    返回:
        list: 股票代號列表
    """
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 取前number個股票代號
    symbols = [item['symbol'] for item in data[:number]]
    return symbols

def prepare_stock_info():
    # 取得前10個公司的股票代號
    s = get_top_company_symbol(top_company_file, top_company_count)

    # 使用字典儲存所有公司的歷史資料
    stock_data_dict = {}

    # 對每個股票代號執行get_stock_info並儲存
    for symbol in s:
        print(f"\n{'='*80}")
        df = get_stock_info(symbol, start_date, end_date)
        stock_data_dict[symbol] = df
        print(f"{'='*80}\n")

    # 返回儲存的資料
    return stock_data_dict

def get_annual_result(symbol, start, end):
    df = get_stock_info(symbol, start, end)

    # 計算漲跌幅
    start_price = df['Close'].iloc[0]
    end_price = df['Close'].iloc[-1]
    change_percent = (end_price - start_price) / start_price * 100

    print(f"股票代碼: {symbol}", f"起始價格: ${start_price:.2f}", f"結束價格: ${end_price:.2f}", f"漲跌幅: {change_percent:.2f}%")

    return change_percent

def run():
    stock_data_dict = prepare_stock_info()

    # 紀錄持有的股票: {symbol: {'shares': 數量, 'cost': 總成本}}
    holdings = {}

    # 紀錄交易歷史
    transactions = []

    # 總投資金額
    total_investment = 0

    # 總損益金額
    total_profit = 0

    # 獲取所有交易日期（使用第一個股票的日期作為基準）
    first_symbol = list(stock_data_dict.keys())[0]
    trading_dates = stock_data_dict[first_symbol].index

    # 從第一天開始直到倒數第二天
    for i in range(len(trading_dates) - 1):
        current_date = trading_dates[i]

        for symbol, df in stock_data_dict.items():
            # 檢查該日期是否有資料
            if current_date not in df.index:
                continue

            k_value = df.loc[current_date, 'K']
            close_price = df.loc[current_date, 'Close']

            # 跳過 NaN 值
            if pd.isna(k_value) or pd.isna(close_price):
                continue

            # 買入策略: K < 20
            if k_value < 20:
                # 買入一股
                cost = close_price
                total_investment += cost

                if symbol not in holdings:
                    holdings[symbol] = {'shares': 0, 'cost': 0}

                holdings[symbol]['shares'] += 1
                holdings[symbol]['cost'] += cost

                transactions.append({
                    'date': current_date,
                    'symbol': symbol,
                    'action': 'BUY',
                    'shares': 1,
                    'price': close_price,
                    'amount': cost,
                    'k_value': k_value
                })
                print(f"[{current_date.date()}] 買入 {symbol} 1股 @ ${close_price:.2f} (K={k_value:.2f})")

            # 賣出策略: K > 80
            elif k_value > 80 and symbol in holdings and holdings[symbol]['shares'] > 0:
                # 賣出全部持股
                shares = holdings[symbol]['shares']
                cost_basis = holdings[symbol]['cost']
                revenue = close_price * shares
                profit = revenue - cost_basis
                total_profit += profit

                transactions.append({
                    'date': current_date,
                    'symbol': symbol,
                    'action': 'SELL',
                    'shares': shares,
                    'price': close_price,
                    'amount': revenue,
                    'profit': profit,
                    'k_value': k_value
                })
                print(f"[{current_date.date()}] 賣出 {symbol} {shares}股 @ ${close_price:.2f} (K={k_value:.2f}) 損益: ${profit:.2f}")

                # 清空持股
                holdings[symbol] = {'shares': 0, 'cost': 0}

    # 最後一天，賣出所有剩餘持股
    last_date = trading_dates[-1]
    print(f"\n{'='*80}")
    print(f"最後一天 [{last_date.date()}] 結算所有持股:")
    print(f"{'='*80}")

    for symbol, holding in holdings.items():
        if holding['shares'] > 0:
            df = stock_data_dict[symbol]
            if last_date in df.index:
                close_price = df.loc[last_date, 'Close']
                shares = holding['shares']
                cost_basis = holding['cost']
                revenue = close_price * shares
                profit = revenue - cost_basis
                total_profit += profit

                transactions.append({
                    'date': last_date,
                    'symbol': symbol,
                    'action': 'SELL_FINAL',
                    'shares': shares,
                    'price': close_price,
                    'amount': revenue,
                    'profit': profit
                })
                print(f"[{last_date.date()}] 賣出 {symbol} {shares}股 @ ${close_price:.2f} 損益: ${profit:.2f}")

    # 計算報酬率
    return_rate = (total_profit / total_investment * 100) if total_investment > 0 else 0

    # 輸出最終統計
    print(f"\n{'='*80}")
    print("交易統計摘要")
    print(f"{'='*80}")
    print(f"總投資金額: ${total_investment:,.2f}")
    print(f"總損益金額: ${total_profit:,.2f}")
    print(f"報酬率: {return_rate:.2f}%")
    print(f"交易次數: {len(transactions)}")
    print(f"{'='*80}\n")
    print(f"S&P 500 一年漲跌幅: {get_annual_result('^GSPC', start_date, end_date):.2f}%")
    print(f"VOO 一年漲跌幅: {get_annual_result('VOO', start_date, end_date):.2f}%")
    print(f"{'='*80}\n")

    return {
        'stock_data': stock_data_dict,
        'transactions': transactions,
        'total_investment': total_investment,
        'total_profit': total_profit,
        'return_rate': return_rate
    }