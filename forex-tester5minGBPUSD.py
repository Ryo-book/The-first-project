import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# ==========================================
# 【1. 準備ブロック】
# ==========================================

# テストしたいファイルのパスを指定（ここを変えるだけでOK）
file_path = r'C:\market_data\GBPUSD_M5.csv' 

# 1. データの読み込み
try:
    df = pd.read_csv(file_path, header=0, encoding='utf-8')
except UnicodeDecodeError:
    df = pd.read_csv(file_path, header=0, encoding='shift-jis')

# 2. 列名の正規化 (FT/MT4形式を共通化)
rename_dict = {
    '<DTYYYYMMDD>': 'Date', '<TIME>': 'Time',
    '<OPEN>': 'Open', '<HIGH>': 'High', '<LOW>': 'Low', '<CLOSE>': 'Close', '<VOL>': 'TickVol',
    'DATE': 'Date', 'TIME': 'Time', 'OPEN': 'Open', 'HIGH': 'High', 'LOW': 'Low', 'CLOSE': 'Close'
}
df.rename(columns=rename_dict, inplace=True)

# 3. 日付と時間の合体 (5分足・4桁パディング対応)
if 'Date' in df.columns and 'Time' in df.columns:
    time_str = df['Time'].astype(str).str.zfill(4) 
    date_str = df['Date'].astype(str)
    df['Combined_Time'] = pd.to_datetime(date_str + time_str, format='%Y%m%d%H%M', errors='coerce')
    df.dropna(subset=['Combined_Time'], inplace=True)
    df.set_index('Combined_Time', inplace=True)

df = df[['Open', 'High', 'Low', 'Close']].copy()

# ------------------------------------------
# ★自動pips単位判定ロジック
# ------------------------------------------
# 価格が50以下（ユーロドル等）なら 0.0001、それ以上（ドル円等）なら 0.01
if df['Close'].iloc[0] < 50:
    pips_unit = 0.00012
    pair_name = "USD以外（ドルストレート）"
else:
    pips_unit = 0.012
    pair_name = "JPYペア（クロス円）"

# 4. パラメータ設定 (pips単位を掛けて自動調整)
spread = 1.0 * pips_unit           # スプレッド 1.0 pips
slope_threshold = 3.0 * pips_unit   # 傾きしきい値 3.0 pips
stop_loss_limit = -10.0 * pips_unit # 10 pips 損切り
take_profit_limit = 20.0 * pips_unit # 20 pips 利確

# その他設定
start_hour = 16
end_hour = 2  
initial_capital = 100000 
risk_per_trade = 0.01    
max_quantity = 10000000  # 最大100ロット制限

print(f"--- 判定結果: {pair_name} として処理します (1pip = {pips_unit}) ---")


# ==========================================
# 【2. ロジック計算ブロック】
# ==========================================

# 1. 指標の計算
period_rsi = 14
diff_rsi = df['Close'].diff()
gain = diff_rsi.clip(lower=0)
loss = -diff_rsi.clip(upper=0)
avg_gain = gain.rolling(window=period_rsi).mean()
avg_loss = loss.rolling(window=period_rsi).mean()
df['RSI'] = 100 - (100 / (1 + avg_gain / avg_loss))

df['EMA_short'] = df['Close'].ewm(span=20, adjust=False).mean()
df['EMA_long'] = df['Close'].ewm(span=80, adjust=False).mean()
df['EMA_trend'] = df['Close'].ewm(span=200, adjust=False).mean()
df['EMA_slope'] = df['EMA_long'].diff(5) 

# 2. 条件判定
buy_cond = (df['EMA_short'] > df['EMA_long']) & \
           (df['Close'] > df['EMA_trend']) & \
           (df['EMA_slope'] > slope_threshold)

sell_cond = (df['EMA_short'] < df['EMA_long']) & \
            (df['Close'] < df['EMA_trend']) & \
            (df['EMA_slope'] < -slope_threshold)

# 3. 時間帯フィルター
df['hour'] = df.index.hour
if start_hour < end_hour:
    time_filter = (df['hour'] >= start_hour) & (df['hour'] < end_hour)
else:
    time_filter = (df['hour'] >= start_hour) | (df['hour'] < end_hour)

# 4. シグナル生成
df['entry_signal'] = np.nan
df.loc[buy_cond & time_filter, 'entry_signal'] = 1
df.loc[sell_cond & time_filter, 'entry_signal'] = -1
df['signal'] = df['entry_signal'].ffill().fillna(0)


# ==========================================
# 【3. 損益シミュレーションブロック】
# ==========================================

df['diff'] = df['Close'].diff()
df['next_diff'] = df['diff'].shift(-1)
df['profit'] = df['signal'] * df['next_diff']

# SL/TP適用
df['profit_with_sl'] = np.where(df['profit'] < stop_loss_limit, stop_loss_limit, df['profit'])
df['profit_tp_sl'] = df['profit'].clip(lower=stop_loss_limit, upper=take_profit_limit)

# 手数料(スプレッド)計算
df['trade_trigger'] = df['signal'].diff().fillna(0) != 0
df['net_profit_sl'] = df['profit_with_sl'] - (df['trade_trigger'] * spread)

# 資産曲線
df['equity_sl'] = df['net_profit_sl'].cumsum()


# ==========================================
# 【4. 統計・レポートブロック】
# ==========================================

def print_detailed_stats(equity_col_name, label):
    trade_id = (df['signal'] != df['signal'].shift()).cumsum()
    profit_col = equity_col_name.replace('equity', 'net_profit')
    trade_returns = df[df['signal'] != 0].groupby(trade_id)[profit_col].sum()
    
    if len(trade_returns) == 0: return

    wins = trade_returns[trade_returns > 0]
    losses = trade_returns[trade_returns < 0]
    pf = (wins.sum() / abs(losses.sum())) if not losses.empty else float('inf')
    expectancy = trade_returns.mean()
    peak = df[equity_col_name].expanding().max()
    max_dd = (df[equity_col_name] - peak).min()
    rf = (trade_returns.sum() / abs(max_dd)) if max_dd != 0 else 0
    reliability = (expectancy / trade_returns.std()) * np.sqrt(len(trade_returns))

    print(f"\n{'='*40}\n  【{label}】詳細レポート\n{'='*40}")
    print(f"トレード回数: {len(trade_returns)} 回 | 勝率: {len(wins)/len(trade_returns)*100:.1f} %")
    print(f"プロフィット係数: {pf:.2f} | 最終損益: {trade_returns.sum():.4f} 通貨単位")
    print(f"平均利益: {wins.mean() if not wins.empty else 0:.4f} | 平均損失: {losses.mean() if not losses.empty else 0:.4f}")
    print(f"最大ドローダウン: {abs(max_dd):.4f} | 回復係数(RF): {rf:.2f}")
    print(f"信頼性係数: {reliability:.2f}\n{'='*40}")

def simulate_compounding(equity_col_name, cap, risk, max_q):
    trade_id = (df['signal'] != df['signal'].shift()).cumsum()
    profit_col = equity_col_name.replace('equity', 'net_profit')
    trade_returns = df[df['signal'] != 0].groupby(trade_id)[profit_col].sum()
    
    balance = cap
    history = [cap]
    sl_val = abs(stop_loss_limit)

    for pnl in trade_returns:
        quantity = (balance * risk) / sl_val
        if quantity > max_q: quantity = max_q
        balance += (quantity * pnl)
        if balance <= 0: balance = 0; history.append(0); break
        history.append(balance)

    print(f"\n{'*'*40}\n  複利シミュレーション (100ロット上限)\n{'*'*40}")
    print(f"最終口座残高: {int(balance):,} 円")
    print(f"元手からの倍率: {balance/cap:.1f} 倍")
    print(f"{'*'*40}")
    return history

# 実行と出力
print(f"\n--- バックテスト完了 (データ総数: {len(df)} 件) ---")
print_detailed_stats('equity_sl', "10pips損切り導入後")
balance_history = simulate_compounding('equity_sl', initial_capital, risk_per_trade, max_quantity)

# グラフ表示
plt.figure(figsize=(12, 10))
plt.subplot(2, 1, 1)
plt.plot(df['equity_sl'], label='Single Unit (SL Only)', color='blue')
plt.axhline(0, color='red', linestyle='--')
plt.title(f'Performance: {os.path.basename(file_path)}')
plt.legend(); plt.grid(True)

plt.subplot(2, 1, 2)
plt.plot(balance_history, label='Compounding Balance', color='orange', lw=2)
plt.title('Compound Interest Growth')
plt.ylabel('Yen'); plt.grid(True)
plt.tight_layout(); plt.show()