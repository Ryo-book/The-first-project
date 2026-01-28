import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# =========================================================
# 1. CSV読み込み（複数通貨ペア想定）
# =========================================================
currency_pairs = ["USDJPY", "EURUSD", "GBPUSD", "AUDUSD"]
backtest_results = {}

for pair in currency_pairs:
    df = pd.read_csv(f"{pair}.csv")  # CSVは同じフォルダに置く
    backtest_results[pair] = df

# =========================================================
# 2. 累積損益折れ線グラフ
# =========================================================
fig, axes = plt.subplots(2, 2, sharex=True, sharey=True, figsize=(12, 6))

for ax, pair in zip(axes.flatten(), currency_pairs):
    profit = backtest_results[pair]['profit'].values
    ax.plot(profit.cumsum(), color="black", linestyle="dashed", marker="o")
    ax.set_title(pair)

plt.subplots_adjust(wspace=0.3, hspace=0.3)
plt.show()

# =========================================================
# 3. 勝ち・負けトレードの積み上げ棒グラフ（例）
# =========================================================
# 仮に profit>0 を勝ち、profit<=0 を負けとして集計
fig, axes = plt.subplots(2, 2, figsize=(12, 6))

for ax, pair in zip(axes.flatten(), currency_pairs):
    df = backtest_results[pair]
    wins = (df['profit'] > 0).sum()
    losses = (df['profit'] <= 0).sum()
    ax.bar(['Win', 'Lose'], [wins, losses], color=['green', 'red'], alpha=0.7)
    ax.set_title(pair)

plt.subplots_adjust(wspace=0.3, hspace=0.3)
plt.show()

# =========================================================
# 4. 散布図 + 回帰線（例：OPEN vs LOW）
# =========================================================
# USDJPY の例
trans_data = backtest_results["USDJPY"].copy()

# 必要に応じて log に変換
trans_data['log_OPEN'] = np.log(trans_data['<OPEN>'])
trans_data['log_LOW'] = np.log(trans_data['<LOW>'])

plt.figure(figsize=(8,5))
ax = sns.regplot(x='log_OPEN', y='log_LOW', data=trans_data)
ax.set_title("Changes in log(OPEN) versus log(LOW)")
plt.show()


#===================
#これで分析できること
#===================

#戦略の全体成績（累積損益折れ線）
#勝率・負けの偏り（棒グラフ）
#価格変動の傾向や相関（散布図 + 回帰線）
#→ つまり、戦略のパフォーマンス + リスク + 市場の挙動 を俯瞰できるテンプレになっています。

