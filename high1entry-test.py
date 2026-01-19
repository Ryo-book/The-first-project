import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# 1. CSV読み込み & DateTime生成
# ==========================================
file_path = r"C:\market_data\USDJPY_M5.csv"
df = pd.read_csv(file_path)

df = df.rename(columns={
    "<OPEN>": "Open",
    "<HIGH>": "High",
    "<LOW>": "Low",
    "<CLOSE>": "Close"
})

date = pd.to_datetime(df["<DTYYYYMMDD>"].astype(str))
time_str = df["<TIME>"].astype(str).str.zfill(6)

time = (
    pd.to_timedelta(time_str.str[:2].astype(int), unit="h") +
    pd.to_timedelta(time_str.str[2:4].astype(int), unit="m") +
    pd.to_timedelta(time_str.str[4:6].astype(int), unit="s")
)

df["DateTime"] = date + time
df = df.set_index("DateTime")
df = df[["Open", "High", "Low", "Close"]]

# ==========================================
# 2. 5分足作成
# ==========================================
df_5m = df.resample("5min").agg({
    "Open": "first",
    "High": "max",
    "Low": "min",
    "Close": "last"
}).dropna()

# ==========================================
# 3. EMA & トレンド判定
# ==========================================
df_5m["EMA20"] = df_5m["Close"].ewm(span=20, adjust=False).mean()
df_5m["EMA80"] = df_5m["Close"].ewm(span=80, adjust=False).mean()

DIFF_THRESH = 0.03  # 3pips

df_5m["trend_strong"] = (
    (df_5m["EMA20"] > df_5m["EMA80"]) &
    (df_5m["EMA20"] > df_5m["EMA20"].shift(1)) &
    (df_5m["EMA80"] > df_5m["EMA80"].shift(1)) &
    ((df_5m["EMA20"] - df_5m["EMA80"]) > DIFF_THRESH)
)

# ==========================================
# 4. pullback & 連続本数
# ==========================================
df_5m["pullback"] = (
    (df_5m["Close"] < df_5m["Open"]) |
    (df_5m["Close"] < df_5m["Close"].shift(1))
)

df_5m["pb_count"] = (
    df_5m["pullback"]
    .groupby((~df_5m["pullback"]).cumsum())
    .cumcount() + 1
)

df_5m.loc[~df_5m["pullback"], "pb_count"] = 0

# ==========================================
# 5. high1（2〜8本押し目限定）
# ==========================================
df_5m["high1"] = (
    df_5m["pb_count"].shift(1).between(2, 8) &
    (df_5m["Close"] > df_5m["High"].shift(1)) &
    (df_5m["Close"] > df_5m["Close"].shift(1))
)

# ==========================================
# 6. バックテスト（Rベース）
# ==========================================
SL_PIPS = 5
TP_PIPS = 10
pip_size = 0.01

position = None
trades = []

rows = list(df_5m.itertuples())

for i in range(len(rows) - 1):
    row = rows[i]
    next_row = rows[i + 1]

    if position is None:
        if row.high1 and row.trend_strong:
            entry_price = next_row.Open
            position = {
                "entry_time": next_row.Index,
                "entry_price": entry_price,
                "stop": entry_price - SL_PIPS * pip_size,
                "tp": entry_price + TP_PIPS * pip_size
            }
            continue

    if position is not None:
        if next_row.Low <= position["stop"]:
            result = "SL"
            r = -1
        elif next_row.High >= position["tp"]:
            result = "TP"
            r = 2
        else:
            continue

        position.update({
            "exit_time": next_row.Index,
            "result": result,
            "R": r
        })

        trades.append(position)
        position = None

# ==========================================
# 7. 統計データ（Rベース）
# ==========================================
df_trades = pd.DataFrame(trades)

print("トレード数:", len(df_trades))

if not df_trades.empty:
    print(df_trades["result"].value_counts())

    win_rate = (df_trades["R"] > 0).mean()
    print("勝率:", win_rate)

    wins = df_trades[df_trades["R"] > 0]["R"]
    losses = df_trades[df_trades["R"] < 0]["R"]

    avg_win = wins.mean()
    avg_loss = losses.mean()
    expectancy = df_trades["R"].mean()
    std = df_trades["R"].std()

    downside_std = losses.std()
    sortino = expectancy / downside_std if downside_std != 0 else np.nan

    pf = wins.sum() / abs(losses.sum())

    print("平均利益(R):", avg_win)
    print("平均損失(R):", avg_loss)
    print("期待値(R):", expectancy)
    print("標準偏差(R):", std)
    print("ソルティノレシオ:", sortino)
    print("プロフィットファクター:", pf)

    # ==========================================
    # 8. 資金曲線（元手100万円）
    # ==========================================
    INITIAL_CAPITAL = 1_000_000
    RISK_PER_TRADE = 0.01  # 1%

    df_trades["capital_change"] = df_trades["R"] * INITIAL_CAPITAL * RISK_PER_TRADE
    df_trades["equity"] = INITIAL_CAPITAL + df_trades["capital_change"].cumsum()

    df_trades["peak"] = df_trades["equity"].cummax()
    df_trades["drawdown"] = df_trades["equity"] - df_trades["peak"]

    print("最終資金:", int(df_trades["equity"].iloc[-1]))
    print("最大ドローダウン:", int(df_trades["drawdown"].min()))

    plt.figure(figsize=(12, 6))
    plt.plot(df_trades["exit_time"], df_trades["equity"])
    plt.title("Equity Curve (Initial Capital: 1,000,000 JPY)")
    plt.grid(True)
    plt.show()

else:
    print("⚠ トレードなし")
