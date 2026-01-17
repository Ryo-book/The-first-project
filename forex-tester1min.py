import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# --- 1. データの読み込み設定 ---
file_path = r'C:\market_data\USDJPY_M1.csv'

# フォレックステスターの形式に合わせて読み込み
# encodingは、エラーが出る場合は 'shift-jis' か 'utf-8' に切り替えてください
try:
    df = pd.read_csv(file_path, header=0, encoding='utf-8')
except UnicodeDecodeError:
    df = pd.read_csv(file_path, header=0, encoding='shift-jis')

# --- 2. 列名の正規化 (前と同じ) ---
rename_dict = {
    '<DTYYYYMMDD>': 'Date', '<TIME>': 'Time',
    '<OPEN>': 'Open', '<HIGH>': 'High', '<LOW>': 'Low', '<CLOSE>': 'Close', '<VOL>': 'TickVol',
    'DATE': 'Date', 'TIME': 'Time', 'OPEN': 'Open', 'HIGH': 'High', 'LOW': 'Low', 'CLOSE': 'Close'
}
df.rename(columns=rename_dict, inplace=True)

# --- 3. 【修正ポイント】日付と時間を正しく合体させる ---
if 'Date' in df.columns and 'Time' in df.columns:
    # 時間(Time)を6桁の文字列に揃える (例: 0 -> 000000, 100 -> 000100)
    time_str = df['Time'].astype(str).str.zfill(6)
    # 日付(Date)を文字列にする
    date_str = df['Date'].astype(str)
    
    # 合体させて日付型に変換 (YYYYMMDDHHMMSS の形式を指定)
    df['Combined_Time'] = pd.to_datetime(date_str + time_str, format='%Y%m%d%H%M%S', errors='coerce')
    
    # 万が一変換に失敗した行（空行など）があれば消す
    df.dropna(subset=['Combined_Time'], inplace=True)
    
    df.set_index('Combined_Time', inplace=True)

# 必要な列が揃っているか確認し、余計な列（<TICKER>等）を捨てる
df = df[['Open', 'High', 'Low', 'Close']].copy()

print("--- データの読み込みと整形に成功しました ---")
print(df.head())

# --- 4. パラメータ設定 ---
spread = 0.002 # 0.2pips
slope_threshold = 0.09

# --- 5. 指標の計算 (Pandasメイン) ---

# RSIの計算（期間14）
period_rsi = 14
diff_rsi = df['Close'].diff()
gain = diff_rsi.clip(lower=0)
loss = -diff_rsi.clip(upper=0)
avg_gain = gain.rolling(window=period_rsi).mean()
avg_loss = loss.rolling(window=period_rsi).mean()
df['RSI'] = 100 - (100 / (1 + avg_gain / avg_loss))

# EMAの計算
df['EMA5'] = df['Close'].ewm(span=5, adjust=False).mean()
df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()

# EMA20の角度
df['EMA20_slope'] = df['EMA20'].diff(5) 

# --- 6. シグナルの判定 ---
# 順張りロジック（短期>中期 且つ 長期より上 且つ 角度あり 且つ RSI過熱なし）
buy_cond = (df['EMA5'] > df['EMA20']) & \
           (df['Close'] > df['EMA200']) & \
           (df['EMA20_slope'] > slope_threshold) & \
           (df['RSI'] < 70)

sell_cond = (df['EMA5'] < df['EMA20']) & \
            (df['Close'] < df['EMA200']) & \
            (df['EMA20_slope'] < -slope_threshold) & \
            (df['RSI'] > 30)

df['signal'] = 0
df.loc[buy_cond, 'signal'] = 1  # 買い
df.loc[sell_cond, 'signal'] = -1 # 売り

# --- 7. 損益計算 ---
df['diff'] = df['Close'].diff()
df['next_diff'] = df['diff'].shift(-1)
df['profit'] = df['signal'] * df['next_diff']

# ドテン・エントリーの瞬間だけスプレッドを引く
df['trade_trigger'] = df['signal'].diff().fillna(0) != 0
df['net_profit'] = df['profit'] - (df['trade_trigger'] * spread)

# 資産曲線の作成
df['equity'] = df['net_profit'].cumsum()

# --- 8. 結果の表示と統計分析 ---
print("\n--- バックテスト完了 ---")
print(f"データ総数: {len(df)} 件")

# トレード結果の抽出
actual_trades = df[df['trade_trigger'] == True]['net_profit']
win_trades = actual_trades[actual_trades > 0]
loss_trades = actual_trades[actual_trades < 0]

# 統計計算
total_trades = len(actual_trades)
win_rate = (len(win_trades) / total_trades * 100) if total_trades > 0 else 0
pf = (win_trades.sum() / abs(loss_trades.sum())) if loss_trades.sum() != 0 else 0

# 最大ドローダウン
peak = df['equity'].expanding().max()
drawdown = df['equity'] - peak
max_dd = drawdown.min()

print(f"トレード回数: {total_trades} 回")
print(f"勝率: {win_rate:.1f} %")
print(f"最終純損益: {df['equity'].iloc[-2]:.2f} 円")
print(f"プロフィットファクター (PF): {pf:.2f}")
print(f"最大ドローダウン: {max_dd:.4f} 円")

# --- 9. グラフ表示 ---
plt.figure(figsize=(12, 6))
df['equity'].plot(title='Forex Tester Backtest Result', grid=True)
plt.axhline(0, color='red', linestyle='--')
plt.ylabel('Profit (Yen)')
plt.show()