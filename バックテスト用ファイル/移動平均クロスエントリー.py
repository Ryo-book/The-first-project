import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =========================
# ① データ読み込み
# =========================
def load_data(path):
    df = pd.read_csv(path)
    
    # 日付＋時刻を datetime に変換
    df["time"] = pd.to_datetime(
        df["<DTYYYYMMDD>"].astype(str) + df["<TIME>"].astype(str).str.zfill(6),
        format="%Y%m%d%H%M%S"
    )
    df = df.sort_values("time").set_index("time")
    
    # CLOSE列を統一
    df["close"] = df["<CLOSE>"]
    
    return df

# =========================
# ② インジケータ計算（EMA20とEMA200）
# =========================
def add_indicators(df, short_span=20, long_span=200):
    df["ema_short"] = df["close"].ewm(span=short_span, adjust=False).mean()
    df["ema_long"]  = df["close"].ewm(span=long_span, adjust=False).mean()
    return df

# =========================
# ③ シグナル生成（ゴールデンクロス/デッドクロス）
# =========================
def generate_signal(df):
    df["signal"] = 0
    df.loc[(df["ema_short"] > df["ema_long"]) & (df["ema_short"].shift(1) <= df["ema_long"].shift(1)), "signal"] = 1
    df.loc[(df["ema_short"] < df["ema_long"]) & (df["ema_short"].shift(1) >= df["ema_long"].shift(1)), "signal"] = -1
    return df

# =========================
# ④ バックテスト本体
# =========================
def backtest(df, spread=0.01):  # スプレッドを引数に追加
    position = 0
    entry_price = 0
    profit_list = []
    equity_curve = []
    cumulative_profit = 0

    for i in range(len(df)):
        price = df["close"].iloc[i]
        signal = df["signal"].iloc[i]
        ema_short = df["ema_short"].iloc[i]
        ema_long = df["ema_long"].iloc[i]

        # エントリー（スプレッド考慮）
        if signal == 1 and position == 0:
            position = 1
            entry_price = price + spread  # ロングは買値にスプレッド加算
        elif signal == -1 and position == 0:
            position = -1
            entry_price = price - spread  # ショートは売値からスプレッド減算

        # 損切り判定
        if position == 1 and ema_short < ema_long:
            profit = price - entry_price
            profit_list.append(profit)
            cumulative_profit += profit
            position = 0
            entry_price = 0
        elif position == -1 and ema_short > ema_long:
            profit = entry_price - price
            profit_list.append(profit)
            cumulative_profit += profit
            position = 0
            entry_price = 0

        # 利確判定（200EMA）
        if position == 1 and price <= ema_long:
            profit = price - entry_price
            profit_list.append(profit)
            cumulative_profit += profit
            position = 0
            entry_price = 0
        elif position == -1 and price >= ema_long:
            profit = entry_price - price
            profit_list.append(profit)
            cumulative_profit += profit
            position = 0
            entry_price = 0

        # エクイティ曲線
        if position == 1:
            equity_curve.append(cumulative_profit + (price - entry_price))
        elif position == -1:
            equity_curve.append(cumulative_profit + (entry_price - price))
        else:
            equity_curve.append(cumulative_profit)

    df["equity"] = equity_curve
    df["trade_profit"] = 0
    trade_idx = df.index[df["signal"] != 0]
    for idx, p in zip(trade_idx, profit_list):
        df.at[idx, "trade_profit"] = p

    return df


# =========================
# ⑤ 成績集計（拡張版）
# =========================
def summarize(df):
    trades = df["trade_profit"].replace(0, np.nan).dropna()
    profits = trades[trades > 0]
    losses = trades[trades < 0]

    total_profit = trades.sum()
    avg_profit = profits.mean() if not profits.empty else 0
    avg_loss = losses.mean() if not losses.empty else 0
    win_rate = (trades > 0).mean() if len(trades) > 0 else 0
    profit_factor = profits.sum() / abs(losses.sum()) if abs(losses.sum()) > 0 else np.nan
    restoration_factor = total_profit / abs(trades.min()) if not trades.empty else np.nan

    # 最大ドローダウン
    cum = df["equity"]
    max_dd = (cum.cummax() - cum).max()

    # シャープレシオ & ソルティノレシオ（日次換算の簡易版）
    returns = cum.diff().fillna(0)
    sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() != 0 else np.nan
    neg_returns = returns[returns < 0]
    downside_std = neg_returns.std() if not neg_returns.empty else 1
    sortino = returns.mean() / downside_std * np.sqrt(252)

    # 期待値・標準偏差
    expectancy = avg_profit * win_rate + avg_loss * (1 - win_rate)
    std_dev = trades.std() if len(trades) > 0 else 0

    return {
        "trades": len(trades),
        "total_profit": total_profit,
        "avg_profit": avg_profit,
        "avg_loss": avg_loss,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "restoration_factor": restoration_factor,
        "max_drawdown": max_dd,
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino,
        "expectancy": expectancy,
        "std_dev": std_dev
    }

# =========================
# ⑥ 可視化
# =========================
def plot_equity(df):
    plt.figure(figsize=(12,6))
    plt.plot(df.index, df["equity"], label="Equity Curve")
    plt.title("EMA20/200 Cross Strategy Equity Curve")
    plt.xlabel("Time")
    plt.ylabel("Profit")
    plt.grid(True)
    plt.legend()
    plt.show()

# =========================
# ⑦ 実行部分
# =========================
if __name__ == "__main__":
    df = load_data(r"C:\Users\Ryouh\OneDrive\デスクトップ\VScode用データ\バックテスト用ファイル\USDJPY_M5.csv")
    df = add_indicators(df, short_span=20, long_span=200)
    df = generate_signal(df)
    df = backtest(df)

    stats = summarize(df)
    # 結果を見やすく表示
    for k, v in stats.items():
        print(f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}")
    
    plot_equity(df)
