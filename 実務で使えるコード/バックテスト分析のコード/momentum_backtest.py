import pandas as pd
import numpy as np
import matplotlib.pyplot as plt   

# =========================
# ① データ読み込み・前処理
# =========================

# CSV読み込み
raw = pd.read_csv(r'C:\market_data\USDJPY_M15.csv')

# datetime を作成（YYYYMMDD + HHMM から datetime 型に変換）
raw['datetime'] = pd.to_datetime(
    raw['<DTYYYYMMDD>'].astype(str) +
    raw['<TIME>'].astype(str).str.zfill(4),
    format='%Y%m%d%H%M'
)

# datetime を index に設定
raw.set_index('datetime', inplace=True)

# CLOSEだけ取り出す（indexはdatetimeのまま）
data = raw[['<CLOSE>']].copy()
data.rename(columns={'<CLOSE>': 'price'}, inplace=True)


# =========================
# ② 戦略ロジック
# =========================

# ① 対数収益率を計算（priceの変化率）
#   log を使う理由：
#   収益率の足し算ができる（累積が簡単になる）
data['returns'] = np.log(data['price'] / data['price'].shift(1))


# ② シンプルな順張り戦略（モメンタム）
#   position = 1  : 買い
#   position = -1 : 売り
#   position = 0  : 無ポジ（ここでは使っていない）
#   np.sign は returns の符号を返す（正なら1、負なら-1、0なら0）
data['position'] = np.sign(data['returns'])


# ③ strategy の収益を計算
#   position.shift(1) を使う理由：
#   「当日の判断で当日トレードする」だと未来の情報を使ってしまうため
#   1つ前のポジションで当日の収益を計算する
data['strategy'] = data['position'].shift(1) * data['returns']


# =========================
# ③ 可視化（資産曲線）
# =========================

# returns と strategy の累積収益（資産曲線）を比較
(
    data[['returns', 'strategy']]
    .dropna()               # NaNを削除（最初の1行がNaNになるため）
    .cumsum()               # 累積和（log収益の累積）
    .apply(np.exp)          # 指数化 → 収益率を元のスケールに戻す
    .plot(
        figsize=(10, 6),
        title='Buy & Hold vs Strategy'
    )
)

plt.show()

#右上にある「↓」で、「専用ターミナルでPythonファイルを実行する。」を選択する



#===============
#このコードの内容
#===============

#「価格データを読み込んで、超単純な順張り戦略のバックテストをして、結果をグラフ化する」ためのもの

#戦略が「市場に勝てているか」を視覚的に判断する。



#===================================
#重要なポイント（理解を深めるために）

#この戦略は超単純すぎるので

#実際の相場では負けやすい

#スプレッドや手数料を考慮していないけど、バックテストの構造を理解するための最初の一歩としては完璧。
#===================================