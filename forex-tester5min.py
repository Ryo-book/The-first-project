import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# --- 1. データの読み込み設定 ---
file_path = r'C:\market_data\USDJPY_M5.csv'

try:
    df = pd.read_csv(file_path, header=0, encoding='utf-8')
except UnicodeDecodeError:
    df = pd.read_csv(file_path, header=0, encoding='shift-jis')

# --- 2. 列名の正規化 (FT/MT4形式をOpen, High, Low, Closeに統一) ---
rename_dict = {
    '<DTYYYYMMDD>': 'Date', '<TIME>': 'Time',
    '<OPEN>': 'Open', '<HIGH>': 'High', '<LOW>': 'Low', '<CLOSE>': 'Close', '<VOL>': 'TickVol',
    'DATE': 'Date', 'TIME': 'Time', 'OPEN': 'Open', 'HIGH': 'High', 'LOW': 'Low', 'CLOSE': 'Close'
}
df.rename(columns=rename_dict, inplace=True)

# --- 3. 日付と時間の合体 (5分足・4桁パディング対応) ---
if 'Date' in df.columns and 'Time' in df.columns:
    time_str = df['Time'].astype(str).str.zfill(4) # 5分足なら4桁(HHMM)で揃える
    date_str = df['Date'].astype(str)
    df['Combined_Time'] = pd.to_datetime(date_str + time_str, format='%Y%m%d%H%M', errors='coerce')
    df.dropna(subset=['Combined_Time'], inplace=True)
    df.set_index('Combined_Time', inplace=True)

# 必要な列だけに絞る
df = df[['Open', 'High', 'Low', 'Close']].copy()

# --- 4. パラメータ設定 ---
spread = 0.004           # 0.4pips (OANDA実質想定)
slope_threshold = 0.03   # EMA角度のしきい値
stop_loss_limit = -0.10  # 10pipsの損切り
take_profit_limit = 0.20 # 20pipsの利確

# --- 5. 指標の計算 (RSI, EMA, Slope) ---

# RSIの計算 (14期間)
period_rsi = 14
diff_rsi = df['Close'].diff()
gain = diff_rsi.clip(lower=0)
loss = -diff_rsi.clip(upper=0)
avg_gain = gain.rolling(window=period_rsi).mean()
avg_loss = loss.rolling(window=period_rsi).mean()
df['RSI'] = 100 - (100 / (1 + avg_gain / avg_loss))

# 複数EMAの計算 (20, 80, 200)
df['EMA_short'] = df['Close'].ewm(span=20, adjust=False).mean()
df['EMA_long'] = df['Close'].ewm(span=80, adjust=False).mean()
df['EMA_trend'] = df['Close'].ewm(span=200, adjust=False).mean()

# EMA80の角度 (5本前との差)
df['EMA_slope'] = df['EMA_long'].diff(5) 

# --- 6. シグナルの判定 (トレンドフォロー + 角度フィルター) ---
# 順張り条件
buy_cond = (df['EMA_short'] > df['EMA_long']) & \
           (df['Close'] > df['EMA_trend']) & \
           (df['EMA_slope'] > slope_threshold)

sell_cond = (df['EMA_short'] < df['EMA_long']) & \
            (df['Close'] < df['EMA_trend']) & \
            (df['EMA_slope'] < -slope_threshold)

# エントリーの瞬間を記録
df['entry_signal'] = np.nan
df.loc[buy_cond, 'entry_signal'] = 1
df.loc[sell_cond, 'entry_signal'] = -1

# ポジションを次のサインまで維持 (ffill)
df['signal'] = df['entry_signal'].ffill().fillna(0)

# --- 7. 損益計算 (ここからが統合・整理されたメインロジック) ---

# 基本の変化量と未来の利益
df['diff'] = df['Close'].diff()
df['next_diff'] = df['diff'].shift(-1)
df['profit'] = df['signal'] * df['next_diff']

# --- 8. 損切り・利確パターンの作成 ---
# パターンA: 10pips損切りのみ (np.whereを使用)
df['profit_with_sl'] = np.where(df['profit'] < stop_loss_limit, stop_loss_limit, df['profit'])

# パターンB: 10pips損切り + 20pips利確 (clip関数を使用)
df['profit_tp_sl'] = df['profit'].clip(lower=stop_loss_limit, upper=take_profit_limit)

# --- 9. 手数料(スプレッド)を引いて純利益にする ---
# シグナルが変化した瞬間（エントリー/ドテン）を特定
df['trade_trigger'] = df['signal'].diff().fillna(0) != 0

# 各パターンの純利益（net_profit）を計算
df['net_profit'] = df['profit'] - (df['trade_trigger'] * spread)
df['net_profit_sl'] = df['profit_with_sl'] - (df['trade_trigger'] * spread)
df['net_profit_tp_sl'] = df['profit_tp_sl'] - (df['trade_trigger'] * spread)

# 資産曲線（equity）の作成
df['equity'] = df['net_profit'].cumsum()
df['equity_sl'] = df['net_profit_sl'].cumsum()
df['equity_tp_sl'] = df['net_profit_tp_sl'].cumsum()

# --- 10. 結果の表示と統計分析 ---

def print_stats(col_name, label):
    profit_col_name = col_name.replace('equity', 'net_profit')
    # トレードが発生した行の損益を抽出
    actual_trades = df.loc[df['trade_trigger'], profit_col_name]
    win_trades = actual_trades[actual_trades > 0]
    loss_trades = actual_trades[actual_trades < 0]
    
    total_trades = len(actual_trades)
    win_count = len(win_trades)
    win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
    pf = (win_trades.sum() / abs(loss_trades.sum())) if loss_trades.sum() != 0 else 0
    
    peak = df[col_name].expanding().max()
    max_dd = (df[col_name] - peak).min()
    
    print(f"\n[{label}]")
    print(f"最終純損益: {df[col_name].iloc[-2]:.2f} 円")
    print(f"トレード回数: {total_trades} 回")
    print(f"勝率: {win_rate:.1f} %")
    print(f"プロフィットファクター (PF): {pf:.2f}")
    print(f"最大ドローダウン: {max_dd:.4f} 円")

print(f"\n--- バックテスト完了 (データ総数: {len(df)} 件) ---")
print_stats('equity', "1. 損切りなし(ドテンのみ)")
print_stats('equity_sl', "2. 10pips損切りのみ")
print_stats('equity_tp_sl', "3. 10p SL + 20p 利確導入")

# --- 11. グラフ表示 ---
plt.figure(figsize=(12, 7))
plt.plot(df['equity'], label='No SL/TP', color='gray', alpha=0.4)
plt.plot(df['equity_sl'], label='10p SL Only', color='blue', alpha=0.6)
plt.plot(df['equity_tp_sl'], label='10p SL + 20p TP', color='green', lw=2)
plt.axhline(0, color='red', linestyle='--')
plt.title('Strategy Comparison: Impact of SL and TP (5Y Backtest)')
plt.ylabel('Profit (Yen)')
plt.legend()
plt.grid(True)
plt.show()