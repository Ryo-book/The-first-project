import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# =========================
# ① データ読み込み（完全修正版）
# =========================
def load_data(path):
    df = pd.read_csv(path)

    # 列名正規化
    df.columns = (
        df.columns
        .str.lower()
        .str.replace("<", "", regex=False)
        .str.replace(">", "", regex=False)
    )

    # 正しい日付列を使う（重要）
    if "dtyyyymmdd" in df.columns:
        df["date"] = pd.to_datetime(df["dtyyyymmdd"], format="%Y%m%d")
        df = df.set_index("date")
    else:
        raise ValueError("dtyyyymmdd 列が見つかりません")

    df = df.sort_index()
    return df


# =========================
# ② 週情報の付加
# =========================
def add_week_info(df):
    df["weekday"] = df.index.weekday  # 月=0
    df["week"] = df.index.to_period("W-FRI")
    return df


# =========================
# ③ エントリー条件
# =========================
def generate_signal(df):
    df["entry"] = False

    for week, wdf in df.groupby("week"):
        if wdf["weekday"].nunique() < 5:
            continue

        mon = wdf[wdf["weekday"] == 0]
        tue = wdf[wdf["weekday"] == 1]
        wed = wdf[wdf["weekday"] == 2]
        thu = wdf[wdf["weekday"] == 3]
        fri = wdf[wdf["weekday"] == 4]

        if mon.empty or fri.empty:
            continue

        max_mon_thu_close = pd.concat([mon, tue, wed, thu])["close"].max()

        if fri["close"].iloc[0] > max_mon_thu_close:
            df.loc[mon.index[0], "entry"] = True

    print("シグナル数:", df["entry"].sum())
    return df


# =========================
# ④ バックテスト
# =========================
def backtest(df, spread_pips=1, pip_value=0.01):
    trades = []

    for entry_time in df[df["entry"]].index:
        # 月曜寄り付き（Ask想定）
        entry_price = df.loc[entry_time, "open"] + spread_pips * pip_value

        # 水曜終値（Bid想定）
        exit_time = entry_time + pd.Timedelta(days=2)
        if exit_time not in df.index:
            continue

        exit_price = df.loc[exit_time, "close"] - spread_pips * pip_value

        profit = exit_price - entry_price

        trades.append({
            "entry_time": entry_time,
            "exit_time": exit_time,
            "profit": profit
        })

    return pd.DataFrame(trades)



# =========================
# ⑤ 成績集計
# =========================
def summarize(trades):
    if trades.empty:
        print("結果: トレードなし")
        return {}

    profits = trades["profit"]
    wins = profits[profits > 0]
    losses = profits[profits < 0]

    equity = profits.cumsum()
    drawdown = equity - equity.cummax()

    return {
        "トレード回数": len(profits),
        "勝率": (profits > 0).mean(),
        "PF": wins.sum() / abs(losses.sum()) if not losses.empty else np.inf,
        "最大DD": drawdown.min(),
        "期待値": profits.mean()
    }


# =========================
# ⑥ エクイティカーブ
# =========================
def plot_equity_curve(trades):
    if trades.empty:
        print("トレードがありません")
        return

    plt.figure(figsize=(12, 4))
    plt.plot(trades["profit"].cumsum())
    plt.title("Equity Curve")
    plt.grid(True)
    plt.show()


# =========================
# ⑦ 実行
# =========================
if __name__ == "__main__":
    df = load_data(
        r"C:\Users\Ryouh\OneDrive\デスクトップ\VScode用データ\バックテスト用ファイル\USDJPY_1D.csv"
    )

    df = add_week_info(df)
    df = generate_signal(df)
    trades = backtest(df)

    print(trades.head())
    stats = summarize(trades)
    for k, v in stats.items():
        print(k, ":", v)

    plot_equity_curve(trades)


print("トレード数:", len(trades))
print("合計損益:", trades["profit"].sum())
