import yfinance as yf
import pandas as pd

# 1. Yahoo!ファイナンスからアップル(AAPL)のデータを取得
# 本のデータに合わせて2010年から2020年くらいまでのデータを取ってみます
symbol = 'AAPL'
df = yf.download(symbol, start='2010-01-01', end='2020-12-31')

# 2. 本のデータ形式（Eikon風）に少し近づける
# 本では「終値(Close)」を使っていることが多いので、Closeだけ抜き出す
# また、列名を本っぽく 'AAPL.O' に変えておくと、後のコードが書きやすいです
data = df[['Close']].rename(columns={'Close': 'AAPL.O'})

# 3. CSVファイルとして保存する
# これで本と同じように pd.read_csv('tr_eikon_eod_data.csv') ができるようになります
data.to_csv('tr_eikon_eod_data.csv')

print("Yahoo!ファイナンスからデータを取得し、'tr_eikon_eod_data.csv' として保存しました！")
print(data.head())


#######################################
#株価や為替のデータを取得できるコードがこれ
#######################################