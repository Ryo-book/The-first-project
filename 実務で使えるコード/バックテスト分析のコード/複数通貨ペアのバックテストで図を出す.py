import matplotlib.pyplot as plt
import pandas as pd

# 通貨ペア
currency_pairs = ["USDJPY", "EURUSD", "GBPUSD", "AUDUSD"]

# CSV読み込み
backtest_results = {}
for pair in currency_pairs:
    df = pd.read_csv(f"{pair}.csv")  # 同じフォルダにCSVを置く
    backtest_results[pair] = df['profit'].values  # profit列を配列に変換

# サブプロット作成
fig, axes = plt.subplots(2, 2, sharex=True, sharey=True, figsize=(10,6))

for ax, pair in zip(axes.flatten(), currency_pairs):
    profit = backtest_results[pair]
    ax.plot(profit.cumsum(), color="black", linestyle="dashed")  # 累積損益曲線
    ax.set_title(pair)

plt.subplots_adjust(wspace=0.3, hspace=0.3)
plt.show()



#===============================================
#1つのFigureに4通貨ペアの累積損益をまとめて表示可能
#===============================================

#通貨ペアがもっと多い場合は plt.subplots(nrows, ncols) を増やすか、nrows=ceil(N/列数) のように自動調整
#あとはこれに、インジケーターや時間軸のコードを付け足していくだけ