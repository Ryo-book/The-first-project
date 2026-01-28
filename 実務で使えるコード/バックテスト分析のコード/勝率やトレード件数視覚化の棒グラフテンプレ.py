import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# ===========================================
# 例データ
# ===========================================
currency_pairs = ["USDJPY", "EURUSD", "GBPUSD", "AUDUSD"]
# 勝ちトレード数の例（仮データ）
win_trades = [35, 28, 40, 32]
# 負けトレード数の例（仮データ）
lose_trades = [15, 22, 10, 18]

# DataFrame化
df = pd.DataFrame({
    "Win": win_trades,
    "Lose": lose_trades
}, index=currency_pairs)

# ===========================================
# サブプロット作成（縦棒と横棒）
# ===========================================
fig, axes = plt.subplots(2, 1, figsize=(8,6))

# 縦棒グラフ（勝敗比較）
df.plot.bar(ax=axes[0], color=["green", "red"], alpha=0.7)
axes[0].set_title("Currency Pair Win/Lose Trades (Vertical Bar)")
axes[0].set_ylabel("Number of Trades")

# 横棒グラフ（同じデータ）
df.plot.barh(ax=axes[1], color=["green", "red"], alpha=0.7)
axes[1].set_title("Currency Pair Win/Lose Trades (Horizontal Bar)")
axes[1].set_xlabel("Number of Trades")

# グラフ間隔調整
plt.tight_layout()
plt.show()


#=========
#できること
#=========

#1通貨ペアごとの勝敗比較
#2縦棒・横棒両方で表示可能
#3色やラベルのカスタマイズが簡単
#4データを入れ替えれば、月別損益や戦略比較 などにも応用可能

#df.plot.bar() は 縦棒
#df.plot.barh() は 横棒
#color を通貨ペアや勝敗ごとに変えられる
#alpha で透明度を調整可能