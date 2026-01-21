import matplotlib.pyplot as plt
import numpy as np
from position_generation import generate_position
from load_data import load_data

def plot_cumret_comparison(data):
    data['returns'] = np.log(data['price'] / data['price'].shift(1))
    data['strategy'] = data['position'].shift(1) * data['returns']
    data.dropna(inplace=True)

    data[['returns', 'strategy']].cumsum().apply(np.exp).plot(figsize=(10, 6))
    plt.title("Cumulative Returns: Market vs Strategy")
    plt.show()

if __name__ == "__main__":
    path = r'C:\market_data\USDJPY_M15.csv'
    data = generate_position(load_data(path))
    plot_cumret_comparison(data)


#===============
#累積リターン比較
#===============
