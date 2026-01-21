import matplotlib.pyplot as plt
from position_generation import generate_position
from load_data import load_data
import numpy as np

def plot_return_hist(data):
    data['returns'] = np.log(data['price'] / data['price'].shift(1))
    data.dropna(inplace=True)

    data['returns'].hist(bins=35, figsize=(10, 6))
    plt.title("Log Return Distribution")
    plt.show()

if __name__ == "__main__":
    path = r'C:\market_data\USDJPY_M15.csv'
    data = generate_position(load_data(path))
    plot_return_hist(data)


#===================
#対数収益率の度数分布
#===================