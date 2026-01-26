


# data_sanity_check.py
def check_group_size(df, col):
    for k, g in df.groupby(col):
        print(f"{k}: rows={len(g)}")



#毎回必須ではない。でも
#複数通貨/複数時間足/長期検証
#をやるなら,入れておくと事故防止になる


#保存すると得するケース
#↓
#複数通貨を扱う・複数時間足を扱う・長期間バックテストする・CSVを頻繁に入れ替える
#👉 データ事故の防止


#例① 通貨ペアごとのデータ量確認（超重要）
for (symbol, g) in df.groupby('symbol'):
    print(f"{symbol:10s} rows={len(g)}")
#👉 USDJPY だけデータ少ない、みたいなのを即発見できる。

#例② 時間足ごとの確認
for (tf, g) in df.groupby('timeframe'):
    print(f"{tf:5s} rows={len(g)}")
#👉 M1 と H1 が混ざってないかチェック。

#例④ EAロジック別（複数ルールある場合）
for (rule_id, g) in df.groupby('rule_id'):
    print(f"rule {rule_id}: trades={len(g)}")
#👉 勝ってるように見えて
#👉 実は 5トレードしかない、を防ぐ。



#これを使うタイミング

#CSV読み込み
#↓
#この確認コード ← ★ここ
#↓
#欠損処理・前処理


#==================================================

#別のファイルでこれを書いて実行して上のコードと連携する

import pandas as pd
from data_sanity_check import check_group_size

df = pd.read_csv("price.csv")

check_group_size(df, 'symbol', '通貨ペア')
check_group_size(df, 'timeframe', '時間足')
check_group_size(df, 'rule_id', 'EAロジック')

# ↓ ここから前処理・EAロジック
