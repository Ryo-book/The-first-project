import pandas as pd

# ① データを作る（読み込む）
data = pd.read_csv(
    'https://hilpisch.com/pyalgo_eikon_eod_data.csv',
    index_col=0,
    parse_dates=True
).dropna()

# ② 保存先フォルダがなければ作る（重要）
import os
os.makedirs('data', exist_ok=True)

# ③ ファイルに書き出す
data.to_csv('data/aapl.csv')
data.to_json('data/aapl.json')

print('CSV export finished')


#========================================================
#Googleスプレッドシートやエクセルにインポートするためのコード
#========================================================

#使う用途
#① バックテスト前の「データ固定」
#② EA開発前の「検証用データ生成」
#③ データ加工の「中間成果物保存」
#④ AI・機械学習用データ作成
#⑤ データの「スナップショット保存」