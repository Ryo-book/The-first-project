import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# ==========================================
# 【1. 設定・準備ブロック】
# ==========================================
file_path = r'C:\market_data\EURUSD_M5.csv' 

# --- パラメータ設定 ---
SPREAD_PIPS = 1.0           # スプレッド(pips)
SL_PIPS = 12.0              # 損切り幅(pips)
TP_PIPS = 24.0              # 利確幅(pips)
SLOPE_THRESH_PIPS = 2.0     # 傾きフィルター(pips換算)
RISK_PERCENT = 0.01         # 1トレードの許容損失(1%)
INITIAL_CAPITAL = 100000    # 初期資金(円)
MAX_LOTS = 100.0            # 最大ロット

# --- 通貨ペア特性の自動判定 ---
# データの最初の数行だけ読み込んで判定（errors='ignore'を削除）
try:
    temp_df = pd.read_csv(file_path, nrows=5, header=0, encoding='utf-8')
except:
    temp_df = pd.read_csv(file_path, nrows=5, header=0, encoding='shift-jis')

# 列名クリーニング（カッコを除去して大文字化）
temp_df.columns = [c.replace('<','').replace('>','').upper() for c in temp_df.columns]

# CLOSE列を探してサンプル価格を取得
if 'CLOSE' in temp_df.columns:
    price_sample = temp_df['CLOSE'].iloc[0]
else:
    # 列名が見つからない場合のフォールバック（最初の数値列を探すなど）
    price_sample = temp_df.select_dtypes(include=[np.number]).iloc[0, 0]

if price_sample < 50:
    PIPS_UNIT = 0.0001      # EURUSD等
    PIP_VALUE_JPY = 1500    # 1ロットで1pip動いた時の円価値 (10ドル×150円想定)
    pair_label = "EURUSD (ドルストレート)"
else:
    PIPS_UNIT = 0.01        # USDJPY等
    PIP_VALUE_JPY = 1000    # 1ロットで1pip動いた時の円価値 (1000円)
    pair_label = "USDJPY/CrossJPY (円ペア)"

SLOPE_THRESH = SLOPE_THRESH_PIPS * PIPS_UNIT

# 1. 本データの読み込み
try:
    df = pd.read_csv(file_path, header=0, encoding='utf-8')
except:
    df = pd.read_csv(file_path, header=0, encoding='shift-jis')

# 列名正規化
rename_dict = {
    '<DTYYYYMMDD>':'Date','<TIME>':'Time','<OPEN>':'Open','<HIGH>':'High','<LOW>':'Low','<CLOSE>':'Close',
    'DATE':'Date', 'TIME':'Time', 'OPEN':'Open', 'HIGH':'High', 'LOW':'Low', 'CLOSE':'Close'
}
df.rename(columns=rename_dict, inplace=True, errors='ignore')

if 'Date' in df.columns:
    # Timeが数値（4桁）の場合に備えてzfill
    df['Time'] = pd.to_datetime(df['Date'].astype(str) + df['Time'].astype(str).str.zfill(4), format='%Y%m%d%H%M', errors='coerce')
    df.dropna(subset=['Time'], inplace=True)
    df.set_index('Time', inplace=True)

df = df[['Open', 'High', 'Low', 'Close']].copy()

# ==========================================
# 【2. インジケータ・シグナル計算ブロック】
# ==========================================

df['EMA_short'] = df['Close'].ewm(span=20, adjust=False).mean()
df['EMA_long'] = df['Close'].ewm(span=80, adjust=False).mean()
df['EMA_trend'] = df['Close'].ewm(span=200, adjust=False).mean()
df['EMA_slope'] = df['EMA_long'].diff(5)

# 時間帯フィルター
df['hour'] = df.index.hour
time_filter = (df['hour'] >= 16) | (df['hour'] < 2)

# ロジック：押し目買い・戻り売り
buy_cond = (df['Close'] > df['EMA_trend']) & \
           (df['EMA_short'] > df['EMA_long']) & \
           (df['Close'] < df['EMA_short']) & \
           (df['EMA_slope'] > SLOPE_THRESH) & time_filter

sell_cond = (df['Close'] < df['EMA_trend']) & \
            (df['EMA_short'] < df['EMA_long']) & \
            (df['Close'] > df['EMA_short']) & \
            (df['EMA_slope'] < -SLOPE_THRESH) & time_filter

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
    
    for i in range(1, len(df)):
        if curr_pos != 0:
            exit_price = 0
            reason = ""
            
            if curr_pos == 1:
                sl_price = entry_price - (SL_PIPS * PIPS_UNIT)
                tp_price = entry_price + (TP_PIPS * PIPS_UNIT)
                if lows[i] <= sl_price:
                    exit_price = sl_price
                    reason = "SL"
                elif highs[i] >= tp_price:
                    exit_price = tp_price
                    reason = "TP"
                elif signals[i] == -1:
                    exit_price = opens[i]
                    reason = "Reverse"
            else:
                sl_price = entry_price + (SL_PIPS * PIPS_UNIT)
                tp_price = entry_price - (TP_PIPS * PIPS_UNIT)
                if highs[i] >= sl_price:
                    exit_price = sl_price
                    reason = "SL"
                elif lows[i] <= tp_price:
                    exit_price = tp_price
                    reason = "TP"
                elif signals[i] == 1:
                    exit_price = opens[i]
                    reason = "Reverse"
            
            if exit_price != 0:
                pips_diff = (exit_price - entry_price) * curr_pos / PIPS_UNIT
                net_pips = pips_diff - SPREAD_PIPS
                # 円貨換算利益
                profit_yen = net_pips * PIP_VALUE_JPY * lots
                
                balance += profit_yen
                trades.append({
                    'entry_time': entry_time, 'exit_time': times[i],
                    'type': 'BUY' if curr_pos == 1 else 'SELL',
                    'pips': net_pips, 'profit': profit_yen, 'balance': balance, 'reason': reason
                })
                curr_pos = 0
                history.append(balance)
                if balance <= 0: break
                continue

        if curr_pos == 0 and signals[i] != 0:
            risk_amount = balance * RISK_PERCENT
            # ロット算出：許容損失額 / (損切りpips * 1pipの価値)
            # 例: 1000円のリスク / (12pips * 1500円) = 0.055ロット
            lots = risk_amount / (SL_PIPS * PIP_VALUE_JPY)
            if lots > MAX_LOTS: lots = MAX_LOTS
            
            if lots > 0.01:
                curr_pos = signals[i]
                entry_price = opens[i]
                entry_time = times[i]
                
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
    print(f"  {pair_label} 実運用検証レポート")
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
    plt.plot(b_hist, color='blue', lw=1.5)
    plt.title(f'{pair_label} Equity Curve')
    plt.grid(True)

    plt.subplot(2, 1, 2)
    plt.hist(tdf['pips'], bins=50, color='gray', alpha=0.7)
    plt.axvline(0, color='red', linestyle='--')
    plt.title('Pips Distribution')
    plt.tight_layout()
    plt.show()

show_report(trade_df, balance_history)