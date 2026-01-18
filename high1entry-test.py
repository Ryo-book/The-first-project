import pandas as pd
import numpy as np

# ==========================================
# 1. CSV読み込み & DateTime生成（5分足）
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
# 2. トレンド判定（5分足 EMA20）
# ==========================================
df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()

df["uptrend"] = (
    (df["Close"] > df["EMA20"]) &
    (df["EMA20"] > df["EMA20"].shift(1))
)

# ==========================================
# 3. high1 定義（5分足）
# ==========================================
# 押し目
df["pullback"] = (
    (df["Close"] < df["Open"]) |
    (df["Close"] < df["Close"].shift(1))
)

# high1
df["high1"] = (
    df["uptrend"] &
    df["pullback"].shift(1) &
    (df["High"] > df["High"].shift(1)) &
    (df["Close"] > df["Close"].shift(1))
)

# ==========================================
# 4. バックテスト（5分足完結）
# ==========================================
SL_PIPS = 10
TP_PIPS = 10
pip_size = 0.01

position = None
trades = []

for i in range(len(df) - 1):

    row = df.iloc[i]
    next_row = df.iloc[i + 1]
    t = df.index[i + 1]

    # エントリー
    if position is None:
        if row["high1"]:
            entry_price = next_row["Open"]
            position = {
                "entry_time": t,
                "entry_price": entry_price,
                "stop": entry_price - SL_PIPS * pip_size,
                "tp": entry_price + TP_PIPS * pip_size
            }
            continue

    # 決済
    if position is not None:
        if next_row["Low"] <= position["stop"]:
            exit_price = position["stop"]
            result = "SL"
        elif next_row["High"] >= position["tp"]:
            exit_price = position["tp"]
            result = "TP"
        else:
            continue

        pnl = exit_price - position["entry_price"]

        position.update({
            "exit_time": t,
            "exit_price": exit_price,
            "pnl": pnl,
            "result": result
        })

        trades.append(position)
        position = None

# ==========================================
# 5. 結果
# ==========================================
df_trades = pd.DataFrame(trades)

print("トレード数:", len(df_trades))
if not df_trades.empty:
    print(df_trades["result"].value_counts())
    print("勝率:", (df_trades["pnl"] > 0).mean())
    print("総損益:", df_trades["pnl"].sum())
else:
    print("⚠ トレードなし")
