import numpy as np
import matplotlib.pyplot as plt
from load_data import load_data

def generate_position(data):
    data['SMA1'] = data['price'].rolling(42).mean()
    data['SMA2'] = data['price'].rolling(252).mean()

    data['position'] = np.where(data['SMA1'] > data['SMA2'], 1, -1)
    data['position'] = data['position'].shift(1)
    data.dropna(inplace=True)

    return data

def plot_position(data):
    data['position'].plot(
        drawstyle='steps-post',
        ylim=[-1.1, 1.1],
        title='Market Positioning',
        figsize=(10, 6)
    )
    plt.show()

if __name__ == "__main__":
    path = r'C:\market_data\USDJPY_M15.csv'
    data = generate_position(load_data(path))
    plot_position(data)


#=============
#ポジション生成
#=============