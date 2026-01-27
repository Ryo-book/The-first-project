#参考　データサイエンスハンドブック　P191

import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("backtest.csv")

# timestampをdatetime化
df["timestamp"] = pd.to_datetime(df["timestamp"])

# profit欠損を除外（念のため）
df = df.dropna(subset=["profit"])

# 時系列順に並べる（同じtimestampならtrade_idで並べる）
df = df.sort_values(["timestamp", "trade_id"])

# 累積損益
cum_profit = df["profit"].cumsum()

# グラフ表示
fig, ax = plt.subplots(figsize=(12,4))
cum_profit.plot(ax=ax)
ax.set_title("Equity Curve")
ax.set_ylabel("Cumulative Profit")
plt.show()

#==============================================================
#資産曲線を正しく描くには dfがトレード順に並んでいる必要があります。

# EX, 取引履歴が「日付順」になっている/「エントリー順」になっている
#など、時系列に並んでいることが必須です。
#==============================================================

