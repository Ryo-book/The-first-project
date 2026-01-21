import pandas as pd

data = pd.read_csv(
    'https://hilpisch.com/pyalgo_eikon_eod_data.csv',
    index_col=0,
    parse_dates=True
).dropna()


data.info()

print(data.tail())

print('AAPL mean:', data['AAPL.O'].mean())
