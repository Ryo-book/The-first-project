import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 1. データの読み込み
file_path = r'C:\vscode用テスト\USDJPYM1.csv'
column_names = ['Time', 'Open', 'High', 'Low', 'Close', 'TickVol', 'Vol', 'Spread']
df = pd.read_csv(file_path, header=None, names=column_names, encoding='utf-16')

# 時間をインデックスに設定
df['Time'] = pd.to_datetime(df['Time'])
df.set_index('Time', inplace=True)

# 2. パラメータ設定
spread = 0.002 # 0.2pips

# 角度のしきい値を設定（0 ではなく 0.001 などにする）
# これにより、横ばいの時のガタガタしたエントリーを切り捨てます
slope_threshold = 0.09



# 1. RSIの計算（期間14）
period_rsi = 14
diff_rsi = df['Close'].diff()
gain = diff_rsi.clip(lower=0) # 上がり幅
loss = -diff_rsi.clip(upper=0) # 下がり幅

# 平均（ここでは簡易的にSMAを使用）
avg_gain = gain.rolling(window=period_rsi).mean()
avg_loss = loss.rolling(window=period_rsi).mean()

# RSI公式
rs = avg_gain / avg_loss
df['RSI'] = 100 - (100 / (1 + rs))

# 3. 指標の計算
df['EMA5'] = df['Close'].ewm(span=5, adjust=False).mean()
df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean() # 長期フィルター

# ★重要：ここで先に 'EMA20_slope' を作ります
df['EMA20_slope'] = df['EMA20'].diff(5) 


# 4. シグナルの判定（すべての武器を合体させる！）

# 買い条件に「強い角度」と「RSIの過熱感なし」を追加
buy_cond = (df['EMA5'] > df['EMA20']) & \
           (df['Close'] > df['EMA200']) & \
           (df['EMA20_slope'] > slope_threshold) & \
           (df['RSI'] < 70)

# 売り条件
sell_cond = (df['EMA5'] < df['EMA20']) & \
            (df['Close'] < df['EMA200']) & \
            (df['EMA20_slope'] < -slope_threshold) & \
            (df['RSI'] > 30)
            

# シグナルをまとめる（ドテン方式を維持しつつ、フィルター外は「何もしない」）
df['signal'] = 0
df.loc[buy_cond, 'signal'] = -1
df.loc[sell_cond, 'signal'] = 1


# 5. 損益計算（これまでと同じ流れ）
df['diff'] = df['Close'].diff()
df['next_diff'] = df['diff'].shift(-1)
df['profit'] = df['signal'] * df['next_diff']



# 6. エントリーの瞬間だけスプレッドを引く
df['trade_trigger'] = df['signal'].diff().fillna(0) != 0
df['net_profit'] = df['profit'] - (df['trade_trigger'] * spread)


# 7. 資産曲線の作成
df['equity'] = df['net_profit'].cumsum()

# --- 結果の表示 ---
print("--- EMAクロス ＋ RSI 50ライン超え  バックテスト完了 ---")
print(f"データ総数: {len(df)} 件")
print(f"実質的なトレード回数: {df['trade_trigger'].sum()} 回")

final_profit = df['equity'].iloc[-2]
print(f"最終純損益: {final_profit:.2f} 円")



# --- グラフ表示 ---
plt.figure(figsize=(10, 6))
df['equity'].plot(title='EMA Cross with Slope Filter', grid=True)
plt.axhline(0, color='red', linestyle='--')
plt.ylabel('Yen')
plt.show()


# --- 勝率と平均損益の分析 ---
# 実際にトレードが発生した行（net_profit が 0 ではない行）だけを抜き出す
actual_trades = df[df['trade_trigger'] == True]['net_profit']

# 勝ちトレードと負けトレードを仕分け
win_trades = actual_trades[actual_trades > 0]
loss_trades = actual_trades[actual_trades < 0]

# 計算
total_trades = len(actual_trades)
win_count = len(win_trades)
win_rate = (win_count / total_trades) * 100 if total_trades > 0 else 0

print(f"\n--- 詳細分析 ---")
print(f"勝率: {win_rate:.1f} %")
print(f"勝ちトレード数: {win_count} 回")
print(f"負けトレード数: {len(loss_trades)} 回")

if win_count > 0:
    print(f"平均利益: {win_trades.mean():.4f} 円")
if len(loss_trades) > 0:
    print(f"平均損失: {loss_trades.mean():.4f} 円")



# --- プロフィットファクター (PF) の計算 ---
total_profit = win_trades.sum()
total_loss = abs(loss_trades.sum()) # 負けの合計（絶対値）

pf = total_profit / total_loss if total_loss > 0 else 0

# --- 最大ドローダウン (MDD) の計算 ---
# 資産曲線のこれまでの最高地点を計算する (NumPyの累積最大値)
peak = df['equity'].expanding().max()
# 最高地点からの下げ幅を計算
drawdown = df['equity'] - peak
# その中での最大（最小値）が最大ドローダウン
max_drawdown = drawdown.min()

print(f"\n--- プロの評価指標 ---")
print(f"プロフィットファクター (PF): {pf:.2f}")
print(f"最大ドローダウン: {max_drawdown:.4f} 円")

# おまけ：ドローダウンをグラフで確認する（これも重要）
# plt.figure(figsize=(10, 4))
# drawdown.plot(title='Drawdown', color='red')
# plt.fill_between(drawdown.index, drawdown, 0, color='red', alpha=0.2)
# plt.show()