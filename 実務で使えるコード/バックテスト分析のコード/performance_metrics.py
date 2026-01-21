import numpy as np
from position_generation import generate_position
from load_data import load_data

def calc_metrics(data):
    data['returns'] = np.log(data['price'] / data['price'].shift(1))
    data['strategy'] = data['position'].shift(1) * data['returns']
    data.dropna(inplace=True)

    annual_return = data[['returns', 'strategy']].mean() * 252
    annual_return_pct = np.exp(annual_return) - 1

    annual_vol = data[['returns', 'strategy']].std() * (252 ** 0.5)

    print("Annual Return:\n", annual_return_pct)
    print("Annual Volatility:\n", annual_vol)

if __name__ == "__main__":
    path = r'C:\market_data\USDJPY_M15.csv'
    data = generate_position(load_data(path))
    calc_metrics(data)


#========================
#年率リターン・年率ボラなど
#========================

