# Python Module with Class
# for Vectorized Backtesting
# of Mean-Reversion Strategies
#
# Python for Algorithmic Trading
# (c) Dr. Yves J. Hilpisch
# The Python Quants GmbH
#

from MomVectorBacktester import *
import numpy as np
import pandas as pd


class MRVectorBacktester(MomVectorBacktester):
    """
    Class for the vectorized backtesting of mean reversion-based trading strategies.
    """

    def __init__(self, symbol=None, start=None, end=None, amount=10000, tc=0.0, csv_path=None):
        # 親クラスの初期化
        super().__init__(symbol, start, end, amount, tc)

        # CSVが指定されたらCSVから読み込む
        if csv_path is not None:
            self.load_csv(csv_path)

    def load_csv(self, csv_path):
        """
        CSVから読み込み、self.dataを作成する
        必要なカラム： Date, Close
        """
        data = pd.read_csv(csv_path)

        # Closeをpriceにコピー
        data['price'] = data['Close']

        # Dateをdatetimeに変換
        data['datetime'] = pd.to_datetime(data['Date'])

        data.set_index('datetime', inplace=True)

        # 価格の対数リターンを作る
        data['return'] = np.log(data['price'] / data['price'].shift(1))
        data.dropna(inplace=True)

        self.data = data

    def run_strategy(self, SMA, threshold):
        """Backtests the trading strategy."""

        data = self.data.copy().dropna()

        # SMA
        data['sma'] = data['price'].rolling(SMA).mean()
        data['distance'] = data['price'] - data['sma']
        data.dropna(inplace=True)

        # sell signals
        data['position'] = np.where(data['distance'] > threshold, -1, np.nan)

        # buy signals
        data['position'] = np.where(data['distance'] < -threshold, 1, data['position'])

        # crossing of current price and SMA (zero distance)
        data['position'] = np.where(
            data['distance'] * data['distance'].shift(1) < 0,
            0,
            data['position']
        )

        data['position'] = data['position'].ffill().fillna(0)

        data['strategy'] = data['position'].shift(1) * data['return']

        # determine when a trade takes place
        trades = data['position'].diff().fillna(0) != 0

        # subtract transaction costs from return when trade takes place
        data.loc[trades, 'strategy'] -= self.tc

        # cumulative returns
        data['creturns'] = self.amount * data['return'].cumsum().apply(np.exp)
        data['cstrategy'] = self.amount * data['strategy'].cumsum().apply(np.exp)

        self.results = data

        # absolute performance of the strategy
        aperf = self.results['cstrategy'].iloc[-1]

        # out-/underperformance of strategy
        operf = aperf - self.results['creturns'].iloc[-1]

        return round(aperf, 2), round(operf, 2)


if __name__ == '__main__':
    # ---- ① 既存のティッカー指定（そのまま動く）----
    mrbt = MRVectorBacktester('^GDX', '2010-01-01', '2020-12-31', 10000, 0.0)
    print(mrbt.run_strategy(SMA=25, threshold=5))

    # ---- ② CSV指定（追加）----
    mrbt_csv = MRVectorBacktester(csv_path=r"C:\market_data\USDJPY_M5.csv",
                                  amount=10000, tc=0.0)
    print(mrbt_csv.run_strategy(SMA=25, threshold=5))
