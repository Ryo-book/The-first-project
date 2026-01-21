import SMAVectorBacktester as SMA

smbt = SMA.SMAVectorBacktester('EUR=', 42, 252,
                               '2010-1-1', '2019-12-31')

smabt.run_strategy()

