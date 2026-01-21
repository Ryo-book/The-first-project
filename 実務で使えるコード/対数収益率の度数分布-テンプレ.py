import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

raw = pd.read_csv(r'C:\market_data\USDJPY_M15.csv')

raw

print(raw.head())

raw.info()

data = pd.DataFrame(raw['<CLOSE>'])

data.rename(columns={'<CLOSE>': 'price'}, inplace=True)

data.info()

data['SMA1'] = data['price'].rolling(42).mean()
data['SMA2'] = data['price'].rolling(252).mean()

data.tail()


import matplotlib.pyplot as plt

# スタイル（seabornは入ってないなら別のにする）
plt.style.use('default')  # 例：default / ggplot / classic など

# 保存時の解像度
plt.rcParams['savefig.dpi'] = 300

# フォント
plt.rcParams['font.family'] = 'serif'


raw['datetime'] = pd.to_datetime(
    raw['<DTYYYYMMDD>'].astype(str) +
    raw['<TIME>'].astype(str).str.zfill(4),
    format='%Y%m%d%H%M'
)

raw.set_index('datetime', inplace=True)

# ② data を作る（ここで index が datetime になる）
data = pd.DataFrame(raw['<CLOSE>'])
data.rename(columns={'<CLOSE>': 'price'}, inplace=True)

data.plot(title='USD/JPY | 42 & 252 periods SMAs (15min)', figsize=(10, 6))




# まず data に price を作る（すでにやってるならOK）
data['price'] = raw['<CLOSE>']

# ここで SMA を作る
data['SMA1'] = data['price'].rolling(42).mean()
data['SMA2'] = data['price'].rolling(252).mean()

# そして position を作る
data['position'] = np.where(data['SMA1'] > data['SMA2'], 1, -1)


print(data.head())
print(data.columns)

#P89↓

data['position'] = np.where(data['SMA1'] > data['SMA2'],
                            1, -1)

data['position'] = data['position'].shift(1)   # ここが重要！

data.dropna(inplace=True)

data['position'].plot(drawstyle='steps-post',
                      ylim=[-1.1, 1.1],
                      title='Market Positioning',
                      figsize=(10, 6));

#P89一旦保留↑

#P90↓対数収益率の度数分布

data['returns'] = np.log(data['price'] / data['price'].shift(1))

data['returns'].hist(bins=35, figsize=(10, 6))

#P91↓

data['strategy'] = data['position'].shift(1) * data['returns']

data[['returns', 'strategy']].sum()

data[['returns', 'strategy']].sum().apply(np.exp)

data[['returns', 'strategy']].cumsum().apply(np.exp).plot(figsize=(10, 6))

#P92↓

data[['returns', 'strategy']].mean() * 252

np.exp(data[['returns', 'strategy']].mean() * 252) - 1

data[['returns', 'strategy']].std() * 252 ** 0.5


(data[['returns', 'strategy']].apply(np.exp) - 1).std() * 252 ** 0.5

#P92↓

data['cumret'] = data['strategy'].cumsum().apply(np.exp)

data['cummax'] = data['cumret'].cummax()

data[['cumret', 'cummax']].dropna().plot(figsize=(10, 6));

#P93↓

drawdown = data['cummax'] - data['cumret']

drawdown.max()

temp = drawdown[drawdown == 0]

periods = (temp.index[1:].to_pydatetime() - temp.index[:-1].to_pydatetime())

periods[12:15]

periods.max()


#全て一気にのせたまとめ