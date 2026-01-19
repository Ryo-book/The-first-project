import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# 【1. 設定・準備ブロック】
# ==========================================
file_path = r'C:\market_data\USDJPY_M15.csv'

SPREAD_PIPS = 1.0

# ここからATRでSL/TP
ATR_PERIOD = 14
SL_ATR_MULTIPLIER = 1.5
TP_ATR_MULTIPLIER = 3.0

SLOPE_THRESH_PIPS = 2.0
RISK_PERCENT = 0.01
INITIAL_CAPITAL = 100000
MAX_LOTS = 10.0

# --- データ読み込み ---
try:
    df = pd.read_csv(file_path, header=0, encoding='utf-8')
except:
    df = pd.read_csv(file_path, header=0, encoding='shift-jis')

# 列名正規化
rename_dict = {
    '<DTYYYYMMDD>': 'Date', '<TIME>': 'Time', '<OPEN>': 'Open', '<HIGH>': 'High', '<LOW>': 'Low', '<CLOSE>': 'Close',
    'DATE': 'Date', 'TIME': 'Time', 'OPEN': 'Open', 'HIGH': 'High', 'LOW': 'Low', 'CLOSE': 'Close'
}
df.rename(columns=rename_dict, inplace=True, errors='ignore')

# Time列の作成
if 'Date' in df.columns and 'Time' in df.columns:
    df['Time'] = pd.to_datetime(df['Date'].astype(str) + df['Time'].astype(str).str.zfill(4), format='%Y%m%d%H%M', errors='coerce')
    df.dropna(subset=['Time'], inplace=True)
    df.set_index('Time', inplace=True)

df = df[['Open', 'High', 'Low', 'Close']].copy()

# --- 通貨ペア特性判定 ---
price_sample = df['Close'].iloc[0]
if price_sample < 50:
    PIPS_UNIT = 0.0001
    PIP_VALUE_JPY = 1500
    pair_label = "EURUSD (ドルストレート)"
else:
    PIPS_UNIT = 0.01
    PIP_VALUE_JPY = 1000
    pair_label = "USDJPY (円ペア)"

SLOPE_THRESH = SLOPE_THRESH_PIPS * PIPS_UNIT

# ==========================================
# 【2. インジケータ・シグナル計算ブロック】
# ==========================================
df['EMA_short'] = df['Close'].ewm(span=20, adjust=False).mean()
df['EMA_long'] = df['Close'].ewm(span=80, adjust=False).mean()
df['EMA_trend'] = df['Close'].ewm(span=200, adjust=False).mean()
df['EMA_slope'] = df['EMA_long'].diff(5)

# ---------- ATR ----------
df['TR'] = np.maximum(df['High'] - df['Low'],
                     np.maximum(abs(df['High'] - df['Close'].shift(1)),
                                abs(df['Low'] - df['Close'].shift(1))))
df['ATR'] = df['TR'].rolling(ATR_PERIOD).mean()

# ---------- ADX ----------
df['PlusDM'] = np.where((df['High'] - df['High'].shift(1)) >
                        (df['Low'].shift(1) - df['Low']), 
                        np.maximum(df['High'] - df['High'].shift(1), 0), 0)

df['MinusDM'] = np.where((df['Low'].shift(1) - df['Low']) >
                         (df['High'] - df['High'].shift(1)),
                         np.maximum(df['Low'].shift(1) - df['Low'], 0), 0)

df['TR_smooth'] = df['TR'].rolling(ATR_PERIOD).sum()
df['PlusDM_smooth'] = df['PlusDM'].rolling(ATR_PERIOD).sum()
df['MinusDM_smooth'] = df['MinusDM'].rolling(ATR_PERIOD).sum()

df['PlusDI'] = 100 * (df['PlusDM_smooth'] / df['TR_smooth'])
df['MinusDI'] = 100 * (df['MinusDM_smooth'] / df['TR_smooth'])

df['DX'] = 100 * (abs(df['PlusDI'] - df['MinusDI']) / (df['PlusDI'] + df['MinusDI']))
df['ADX'] = df['DX'].rolling(ATR_PERIOD).mean()

# 24時間稼働 → time_filter無し
# ------------- ADX方向性の追加 -------------
# buy条件
buy_cond = (
    (df['Close'] > df['EMA_trend']) &
    (df['EMA_short'] > df['EMA_long']) &
    (df['Close'] < df['EMA_short']) &
    (df['EMA_slope'] > SLOPE_THRESH) &
    (df['ADX'] > 25) &
    (df['PlusDI'] > df['MinusDI'])   # ここ追加
)

# sell条件
sell_cond = (
    (df['Close'] < df['EMA_trend']) &
    (df['EMA_short'] < df['EMA_long']) &
    (df['Close'] > df['EMA_short']) &
    (df['EMA_slope'] < -SLOPE_THRESH) &
    (df['ADX'] > 25) &
    (df['MinusDI'] > df['PlusDI'])   # ここ追加
)


df['signal'] = 0
df.loc[buy_cond, 'signal'] = 1
df.loc[sell_cond, 'signal'] = -1

# ==========================================
# 【3. 実運用シミュレーションブロック】
# ==========================================
def run_backtest(df):
    balance = INITIAL_CAPITAL
    history = [INITIAL_CAPITAL]
    trades = []

    curr_pos = 0
    entry_price = 0
    entry_time = None
    lots = 0

    times = df.index
    opens = df['Open'].values
    highs = df['High'].values
    lows = df['Low'].values
    closes = df['Close'].values
    signals = df['signal'].values
    atrs = df['ATR'].values

    # デバッグ用
    print("データ数:", len(df))
    print("最初の日時:", times[0])
    print("最後の日時:", times[-1])
    print("シグナル数:", (signals != 0).sum())

    for i in range(2, len(df)):
        # エントリー
        if curr_pos == 0 and signals[i-1] != 0:
            if np.isnan(atrs[i-1]):
                continue

            atr = atrs[i-1]
            sl_pips = atr * SL_ATR_MULTIPLIER / PIPS_UNIT
            tp_pips = atr * TP_ATR_MULTIPLIER / PIPS_UNIT

            risk_amount = balance * RISK_PERCENT
            lots = risk_amount / (sl_pips * PIP_VALUE_JPY)
            if lots > MAX_LOTS:
                lots = MAX_LOTS

            if lots > 0.01:
                curr_pos = signals[i-1]
                entry_price = opens[i]
                entry_time = times[i]
                entry_sl_pips = sl_pips
                entry_tp_pips = tp_pips

        # 決済
        if curr_pos != 0:
            exit_price = 0
            reason = ""
            if curr_pos == 1:
                sl_price = entry_price - (entry_sl_pips * PIPS_UNIT)
                tp_price = entry_price + (entry_tp_pips * PIPS_UNIT)

                if lows[i] <= sl_price:
                    exit_price = sl_price
                    reason = "SL"
                elif highs[i] >= tp_price:
                    exit_price = tp_price
                    reason = "TP"
                elif signals[i-1] == -1:
                    exit_price = opens[i]
                    reason = "Reverse"
            else:
                sl_price = entry_price + (entry_sl_pips * PIPS_UNIT)
                tp_price = entry_price - (entry_tp_pips * PIPS_UNIT)

                if highs[i] >= sl_price:
                    exit_price = sl_price
                    reason = "SL"
                elif lows[i] <= tp_price:
                    exit_price = tp_price
                    reason = "TP"
                elif signals[i-1] == 1:
                    exit_price = opens[i]
                    reason = "Reverse"

            if exit_price != 0:
                pips_diff = (exit_price - entry_price) * curr_pos / PIPS_UNIT
                net_pips = pips_diff - SPREAD_PIPS
                profit_yen = net_pips * PIP_VALUE_JPY * lots

                balance += profit_yen
                trades.append({
                    'entry_time': entry_time, 'exit_time': times[i],
                    'type': 'BUY' if curr_pos == 1 else 'SELL',
                    'pips': net_pips, 'profit': profit_yen, 'balance': balance, 'reason': reason
                })
                curr_pos = 0
                history.append(balance)
                if balance <= 0:
                    print("資金がゼロになりました。終了します。")
                    break

    return pd.DataFrame(trades), history

trade_df, balance_history = run_backtest(df)

# ==========================================
# 【4. レポート表示】
# ==========================================
def show_report(tdf, b_hist):
    if tdf.empty:
        print("トレードが発生しませんでした。設定やデータのパスを確認してください。")
        return

    win_rate = (tdf['pips'] > 0).sum() / len(tdf) * 100
    pos_profit = tdf.loc[tdf['profit'] > 0, 'profit'].sum()
    neg_profit = abs(tdf.loc[tdf['profit'] <= 0, 'profit'].sum())
    pf = pos_profit / neg_profit if neg_profit != 0 else float('inf')

    max_dd = (pd.Series(b_hist).cummax() - pd.Series(b_hist)).max()

    print(f"\n{'='*45}")
    print(f"  {pair_label} 実運用検証レポート (24時間稼働)")
    print(f"{'='*45}")
    print(f"総トレード数   : {len(tdf)} 回")
    print(f"勝率           : {win_rate:.1f} %")
    print(f"プロフィット係数: {pf:.2f}")
    print(f"最大ドローダウン: {int(max_dd):,} 円")
    print(f"最終残高       : {int(b_hist[-1]):,} 円")
    print(f"平均pips(1回)  : {tdf['pips'].mean():.2f} pips")
    print(f"{'='*45}")

    plt.figure(figsize=(12, 8))
    plt.subplot(2, 1, 1)
    plt.plot(b_hist, lw=1.5)
    plt.title(f'{pair_label} Equity Curve')
    plt.grid(True)

    plt.subplot(2, 1, 2)
    plt.hist(tdf['pips'], bins=50, alpha=0.7)
    plt.axvline(0, color='red', linestyle='--')
    plt.title('Pips Distribution')
    plt.tight_layout()
    plt.show()

show_report(trade_df, balance_history)
