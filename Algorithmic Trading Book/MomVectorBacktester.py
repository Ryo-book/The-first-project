import numpy as np
import pandas as pd


class MomVectorBacktester:
    """
    Vectorized backtesting of momentum-based trading strategies.
    （モメンタム戦略のバックテストを高速に行うためのクラス）
    """

    def __init__(self, csv_path, start, end, amount, tc):
        # --- 初期化（最初に一度だけ実行される） ---
        self.csv_path = csv_path          # CSVファイルのパス
        self.start = pd.to_datetime(start)  # 解析開始日
        self.end = pd.to_datetime(end)      # 解析終了日
        self.amount = amount              # 初期投資額
        self.tc = tc                      # 取引コスト（例：0.001 = 0.1%）
        self.results = None               # 結果格納用の変数（後で使う）

        self.get_data()                   # データ取得（CSV読み込み）を実行


    def get_data(self):
        # --- CSVを読み込み、必要な形に整形する ---
        raw = pd.read_csv(self.csv_path)

        # datetime を作る
        raw['datetime'] = pd.to_datetime(
            raw['<DTYYYYMMDD>'].astype(str) +
            raw['<TIME>'].astype(str).str.zfill(4),
            format='%Y%m%d%H%M'
        )

        # datetime を index にする
        raw.set_index('datetime', inplace=True)

        # start/end で期間を絞り込む
        raw = raw.loc[self.start:self.end]

        # Close価格だけを取り出す
        data = raw[['<CLOSE>']].copy()
        data.rename(columns={'<CLOSE>': 'price'}, inplace=True)

        # 対数収益率（return）を計算
        data['return'] = np.log(data['price'] / data['price'].shift(1))

        # NaNを削除（最初の1行はshiftのせいでNaNになる）
        self.data = data.dropna()


    def run_strategy(self, momentum=1):
        # --- 戦略を実行する ---
        data = self.data.copy()  # 元データを汚さないためコピーする

        # position（ポジション）を決める
        # rolling(momentum).mean() = momentum期間の平均リターン
        # np.sign() = 正なら1（買い）、負なら-1（売り）
        data['position'] = np.sign(data['return'].rolling(momentum).mean())

        # strategy（戦略のリターン）を計算
        # positionを1つずらして、翌足から適用する
        data['strategy'] = data['position'].shift(1) * data['return']

        # 取引が発生したタイミングを見つける
        trades = data['position'].diff().fillna(0) != 0

        # 取引が発生した日に手数料を引く
        data.loc[trades, 'strategy'] -= self.tc

        # 累積リターンを計算（資金の増え方を計算）
        data['creturns'] = self.amount * data['return'].cumsum().apply(np.exp)
        data['cstrategy'] = self.amount * data['strategy'].cumsum().apply(np.exp)

        self.results = data  # 結果を保存

        # 最終的な資産額を取得
        aperf = self.results['cstrategy'].iloc[-1]
        # 戦略の成績 - 単純保有の成績
        operf = aperf - self.results['creturns'].iloc[-1]

        return round(aperf, 2), round(operf, 2)


    def plot_results(self):
        # --- 結果をグラフで表示 ---
        if self.results is None:
            print("No results yet. Run strategy first.")
            return

        self.results[['creturns', 'cstrategy']].plot(figsize=(10, 6))


if __name__ == '__main__':
    mombt = MomVectorBacktester(
        csv_path=r"C:\market_data\USDJPY_M5.csv",
        start="2019-12-31",
        end="2025-01-02",
        amount=10000,
        tc=0.001
    )

    print(mombt.run_strategy(momentum=5))
    mombt.plot_results()
