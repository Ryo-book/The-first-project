#P94.ipynb　このファイルでSMAVectorBacktesterを使うために必要なコードファイル


import numpy as np
import pandas as pd

class SMAVectorBacktester:
    def __init__(self, symbol, SMA1, SMA2, start, end):
        self.symbol = symbol
        self.SMA1 = SMA1
        self.SMA2 = SMA2
        self.start = start
        self.end = end

    def get_data(self):
        # ここでCSVを読み込む（例：USDJPY_M15.csv）
        # symbol名に応じてファイルを変えるなら、ここを拡張できる
        raw = pd.read_csv(r'C:\market_data\USDJPY_M15.csv')

        raw['datetime'] = pd.to_datetime(
            raw['<DTYYYYMMDD>'].astype(str) +
            raw['<TIME>'].astype(str).str.zfill(4),
            format='%Y%m%d%H%M'
        )

        raw.set_index('datetime', inplace=True)

        data = pd.DataFrame(raw['<CLOSE>'])
        data.rename(columns={'<CLOSE>': 'Close'}, inplace=True)

        return data

    def run_strategy(self):
        data = self.get_data()

        # SMA計算
        data['SMA1'] = data['Close'].rolling(self.SMA1).mean()
        data['SMA2'] = data['Close'].rolling(self.SMA2).mean()

        # ポジション
        data['position'] = np.where(data['SMA1'] > data['SMA2'], 1, -1)
        data['position'] = data['position'].shift(1)  # 重要：翌足から反映

        # 対数収益率
        data['returns'] = np.log(data['Close'] / data['Close'].shift(1))

        # 戦略収益
        data['strategy'] = data['position'] * data['returns']
        
        # NaNを削除（ここが超重要） SMA計算とposition（ポジション）とreturns（対数収益率）とstrategy（戦略収益）の3つのコードの下にこれを置かないと、どれかが必ずNaNとなってしまう。
        data.dropna(inplace=True)

        # 累積収益
        cumret = data['returns'].cumsum()
        cumstrat = data['strategy'].cumsum()

        print("Running strategy:", self.symbol)
        print("SMA1:", self.SMA1, "SMA2:", self.SMA2)
        print("Period:", self.start, "to", self.end)
        print("cumret:", cumret.iloc[-1])
        print("cumstrat:", cumstrat.iloc[-1])

        return data






#=======================================================
#import SMAVectorBacktester as SMAを読み込むためのファイル
#=======================================================