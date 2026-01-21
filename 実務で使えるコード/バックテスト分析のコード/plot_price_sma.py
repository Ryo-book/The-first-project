import numpy as np
import matplotlib.pyplot as plt
from load_data import load_data

def plot_price_sma(data):
    data['SMA1'] = data['price'].rolling(42).mean()
    data['SMA2'] = data['price'].rolling(252).mean()

    data[['price', 'SMA1', 'SMA2']].plot(
        title='USD/JPY | 42 & 252 periods SMAs (15min)',
        figsize=(10, 6)
    )
    plt.show()

if __name__ == "__main__":
    path = r'C:\market_data\USDJPY_M15.csv'
    data = load_data(path)
    plot_price_sma(data)


#================
#価格とSMAプロット
#================