import yfinance as yf

def get_data_yfinance(ticker, start, end):
    df = yf.download(ticker, start=start, end=end)
    return df

# 例：AAPLを取得
data = get_data_yfinance('AAPL', '2010-01-01', '2019-12-31')
print(data.head())




#==========================================
#🔥 これの良いところ

#銘柄コードを変えるだけでOK

#データの形式がそのままバックテストに使える

#追加ライブラリは yfinance だけ
#==========================================


#=====================
#特に以下の用途に便利：

#複数銘柄のデータ収集(株、指数、コモディティ等も可能)

#バックテスト用データ

#価格の可視化

#機械学習の学習データ
#=====================