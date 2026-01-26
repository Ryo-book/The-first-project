import pandas as pd
import numpy as np


def calc_metrics(g):
    """
    g: 1つのグループ（例: USDJPY / M15 のトレード結果）
    必要列:
      - profit: 各トレードの損益
      - win: 1=勝ち, 0=負け
    """

    # ----------------------------
    # 1) 累積損益（資産曲線のようなもの）
    # ----------------------------
    # 例: [10, -5, 20] → 累積は [10, 5, 25]
    cum_profit = g['profit'].cumsum()

    # ----------------------------
    # 2) 最大ドローダウン
    # ----------------------------
    # running_max: これまでの最大累積損益
    running_max = cum_profit.cummax()

    # drawdown: その時点の最大損失幅
    # 例: running_maxが100で現在が80なら、drawdown=20
    drawdown = running_max - cum_profit

    # max_drawdown: drawdownの最大値（最大下落幅）
    max_drawdown = drawdown.max()

    # ----------------------------
    # 3) 期待値（1トレードあたり平均損益）
    # ----------------------------
    # 例: profitが[1, -1, 3] → 平均=1
    ev = g['profit'].mean()

    # ----------------------------
    # 4) 標準偏差（損益のブレ）
    # ----------------------------
    # 大きいほど損益のブレが大きい（リスクが高い）
    std = g['profit'].std()

    # ----------------------------
    # 5) ソルティノ比率（下振れリスクを考慮した期待値）
    # ----------------------------
    # downside_std: 負けトレードの損益の標準偏差
    downside_std = g[g['profit'] < 0]['profit'].std()

    # sortino: 期待値 / 下振れリスク
    # downside_stdが0の場合は計算不能なのでNaNにする
    sortino = ev / downside_std if downside_std != 0 else np.nan

    # ----------------------------
    # 6) 勝ちトレードの平均損益
    # ----------------------------
    avg_win = g[g['profit'] > 0]['profit'].mean()

    # ----------------------------
    # 7) 負けトレードの平均損益（正の値に変換）
    # ----------------------------
    # profitが負なので - を付けて正にする
    avg_loss = -g[g['profit'] < 0]['profit'].mean()

    # ----------------------------
    # 8) ペイオフレシオ（平均利益 / 平均損失）
    # ----------------------------
    # 例: avg_win=2, avg_loss=1 → payoff_ratio=2
    payoff_ratio = avg_win / avg_loss if avg_loss != 0 else np.nan

    # ----------------------------
    # 9) 結果をまとめて返す
    # ----------------------------
    return pd.Series({
        'win_rate': g['win'].mean(),                 # 勝率（1の割合）
        'expected_value': ev,                        # 期待値（平均損益）
        'total_profit': g['profit'].sum(),           # 総利益（合計損益）
        'win_sum': g[g['profit'] > 0]['profit'].sum(),   # 勝ちの合計利益
        'loss_sum': -g[g['profit'] < 0]['profit'].sum(), # 負けの合計損失（正に変換）
        'avg_win': avg_win,                          # 勝ちトレードの平均損益
        'avg_loss': avg_loss,                        # 負けトレードの平均損益（正の値）
        'payoff_ratio': payoff_ratio,                # ペイオフレシオ
        'trades': g['win'].count(),                  # 総トレード数
        'max_drawdown': max_drawdown,                # 最大ドローダウン
        'std_dev': std,                              # 標準偏差（損益のブレ）
        'sortino': sortino                           # ソルティノ比率
    })


# symbol×timeframeごとにcalc_metricsを実行し、結果をまとめる
result = df.groupby(['symbol','timeframe'], observed=True).apply(calc_metrics)



#=========
#統計データ
#=========

#これは、「トレードの質」を見るのに最強

#====================================================================
#ドローダウンの分析に「drawdown_analysis.py」ファイルがあるが、
#トレード結果があるなら →　こっち
#足データからポジション生成するなら　→　「drawdown_analysis.py」ファイル
#本当に強いEAを作るなら、両方見るのが正解
#====================================================================



# ==========================
# トレード結果の統計（テンプレ）
# ==========================
# 目的:
#   バックテスト結果から「勝率・期待値・ドローダウン」など
#   EAの性能を一気に可視化する
#
# 使う場面:
#   - 複数通貨ペアを同時に検証するとき
#   - 複数時間足で比較するとき
#   - 複数ロジックを比較するとき
#
# 注意:
#   profit, win列が必須


