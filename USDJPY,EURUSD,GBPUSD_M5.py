import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# ==========================================
# 【1. 準備ブロック】
# ==========================================

file_path = r'C:\market_data\USDJPY_M5.csv'

try:
    df = pd.read_csv(file_path, header=0, encoding='utf-8')
except:
    df = pd.read_csv(file_path, header=0, encoding='shift-jis')

rename_dict = {'<DTYYYYMMDD>':'Date','<TIME>':'Time','<OPEN>':'Open','<HIGH>':'High','<LOW>':'Low','<CLOSE>':'Close'}
df.rename(columns=rename_dict, inplace=True, errors='ignore')

if 'Date' in df.columns and 'Time' in df.columns:
    time_str = df['Time'].astype(str).str.zfill(4)
    df['Time'] = pd.to_datetime(df['Date'].astype(str) + time_str, format='%Y%m%d%H%M')
    df.set_index('Time', inplace=True)

df = df[['Open', 'High', 'Low', 'Close']].copy()

# 通貨ペアごとの厳密な設定
price_sample = df['Close'].iloc[0]
if price_sample < 50: 
    pips_unit = 0.0001
    pip_value_per_1lot = 1500  
    pair_label = "USDストレート"
else:
    pips_unit = 0.01
    pip_value_per_1lot = 100   
    pair_label = "クロス円"

# バックテスト・パラメータ
spread_pips = 1.0
slope_threshold = 3.0 * pips_unit
sl_pips = 10.0
initial_capital = 100000
risk_per_trade = 0.01 
max_lot_cap = 100     

# ==========================================
# 【2. ロジック計算ブロック】
# ==========================================

df['EMA_short'] = df['Close'].ewm(span=20, adjust=False).mean()
df['EMA_long'] = df['Close'].ewm(span=80, adjust=False).mean()
df['EMA_trend'] = df['Close'].ewm(span=200, adjust=False).mean()
df['EMA_slope'] = df['EMA_long'].diff(5)

df['hour'] = df.index.hour
time_filter = (df['hour'] >= 16) | (df['hour'] <= 1)

buy_target = (df['EMA_short'] > df['EMA_long']) & (df['Close'] > df['EMA_trend']) & (df['EMA_slope'] > slope_threshold) & time_filter
sell_target = (df['EMA_short'] < df['EMA_long']) & (df['Close'] < df['EMA_trend']) & (df['EMA_slope'] < -slope_threshold) & time_filter

df['target_pos'] = 0
df.loc[buy_target, 'target_pos'] = 1
df.loc[sell_target, 'target_pos'] = -1


# ==========================================
# 【3. トレード実行ブロック】
# スコープ修正・同足エントリー禁止・SL厳密計算
# ==========================================

def run_simulation_final(df, sl_pips, spread_pips, pips_unit, pip_val_1lot, cap, risk, max_lot):
    trades = []
    balance = cap
    history = [cap]
    
    curr_pos = 0 
    current_lot = 0 # 【改善1】スコープを外に出して初期化
    entry_price = 0
    entry_time = None
    
    times = df.index
    closes = df['Close'].values
    highs = df['High'].values
    lows = df['Low'].values
    targets = df['target_pos'].values

    for i in range(len(df)):
        if balance <= 0: break
        
        target = targets[i]
        
        # --- A. ポジション保有中の処理 ---
        if curr_pos != 0:
            exit_executed = False
            net_pips = 0
            exit_price = 0
            
            # 1. 損切り(SL)判定 (最優先)
            if curr_pos == 1: # BUY保有時
                sl_price = entry_price - (sl_pips * pips_unit)
                if lows[i] <= sl_price:
                    exit_price = sl_price
                    # 【改善3】SLヒット時は (SL幅 + スプレッド) を確実に損失にする
                    net_pips = -(sl_pips + spread_pips)
                    exit_executed = True
            else: # SELL保有時
                sl_price = entry_price + (sl_pips * pips_unit)
                if highs[i] >= sl_price:
                    exit_price = sl_price
                    net_pips = -(sl_pips + spread_pips)
                    exit_executed = True
            
            # 2. シグナル反転判定 (SLがヒットしていない場合のみ)
            if not exit_executed and target != curr_pos:
                exit_price = closes[i]
                # 通常決済の損益計算
                raw_pips = (exit_price - entry_price) * curr_pos / pips_unit
                net_pips = raw_pips - spread_pips
                exit_executed = True
            
            if exit_executed:
                trade_profit_yen = net_pips * pip_val_1lot * current_lot
                balance += trade_profit_yen
                
                trades.append({
                    'entry_time': entry_time, 'exit_time': times[i],
                    'entry_price': entry_price, 'exit_price': exit_price,
                    'side': 'BUY' if curr_pos == 1 else 'SELL',
                    'profit_pips': net_pips, 'profit_yen': trade_profit_yen,
                    'balance': balance
                })
                
                curr_pos = 0
                history.append(balance)
                
                # 【改善2】決済・反転が発生した足では「新規建て」を禁止。次の足に回す。
                continue

        # --- B. 新規エントリー判定 ---
        if curr_pos == 0 and target != 0:
            # 損切り時に資金の1%を失うようにロット計算
            risk_amount = balance * risk
            # 損失幅 = SL幅 + スプレッド
            current_lot = risk_amount / ((sl_pips + spread_pips) * pip_val_1lot)
            if current_lot > max_lot: current_lot = max_lot
            
            if current_lot > 0:
                entry_price = closes[i]
                entry_time = times[i]
                curr_pos = target

    return pd.DataFrame(trades), history

# 実行
trade_df, balance_history = run_simulation_final(df, sl_pips, spread_pips, pips_unit, pip_value_per_1lot, initial_capital, risk_per_trade, max_lot_cap)


# ==========================================
# 【4. 統計・レポートブロック】
# ==========================================

def print_final_report(tdf, b_hist):
    if tdf.empty: 
        print("トレードが一度も発生しませんでした。")
        return
    
    wins = tdf[tdf['profit_pips'] > 0]
    loss = tdf[tdf['profit_pips'] <= 0]
    
    # 【改善6】ドローダウン計算を複利ベースの残高履歴から行う
    b_series = pd.Series(b_hist)
    peaks = b_series.cummax()
    drawdowns = b_series - peaks
    max_dd = drawdowns.min()
    
    expectancy_yen = tdf['profit_yen'].mean()
    # ソルティノ用下方偏差
    downside_trades = tdf.loc[tdf['profit_yen'] < 0, 'profit_yen']
    sortino = (expectancy_yen / downside_trades.std()) if len(downside_trades) > 1 else 0
    
    total_profit = b_hist[-1] - b_hist[0]
    rf = total_profit / abs(max_dd) if max_dd != 0 else 0
    sqn = (tdf['profit_yen'].mean() / tdf['profit_yen'].std()) * np.sqrt(len(tdf))

    print(f"\n{'='*45}")
    print(f"  【最終実運用シミュレーション結果】")
    print(f"{'='*45}")
    print(f"■ 通貨ペア: {pair_label}")
    print(f"  総トレード数    : {len(tdf)} 回")
    print(f"  勝率            : {len(wins)/len(tdf)*100:.1f} %")
    print(f"  最終残高        : {int(b_hist[-1]):,} 円")
    print(f"  最大ドローダウン : {int(abs(max_dd)):,} 円")
    print(f"\n■ 損益詳細")
    print(f"  平均利益(1回)   : {int(tdf.loc[tdf['profit_yen']>0, 'profit_yen'].mean()):,} 円")
    print(f"  平均損失(1回)   : {int(tdf.loc[tdf['profit_yen']<0, 'profit_yen'].mean()):,} 円")
    print(f"  期待値(1回)     : {int(expectancy_yen):,} 円")
    print(f"\n■ 評価指標")
    print(f"  プロフィット係数 : {wins['profit_yen'].sum()/abs(loss['profit_yen'].sum()):.2f}")
    print(f"  回復係数(RF)    : {rf:.2f}")
    print(f"  信頼性(SQN)     : {sqn:.2f}")
    print(f"{'='*45}")

print_final_report(trade_df, balance_history)

plt.figure(figsize=(10, 6))
plt.plot(balance_history, color='orange', lw=2)
plt.title('Final Professional Equity Curve')
plt.ylabel('Balance (JPY)')
plt.grid(True)
plt.show()