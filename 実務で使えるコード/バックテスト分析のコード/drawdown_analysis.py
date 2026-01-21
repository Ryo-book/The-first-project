import numpy as np
from position_generation import generate_position
from load_data import load_data

def calc_drawdown(data):
    data['returns'] = np.log(data['price'] / data['price'].shift(1))
    data['strategy'] = data['position'].shift(1) * data['returns']
    data.dropna(inplace=True)

    data['cumret'] = np.exp(data['strategy'].cumsum())
    data['cummax'] = data['cumret'].cummax()
    data['drawdown'] = data['cummax'] - data['cumret']

    max_drawdown = data['drawdown'].max()

    temp = data['drawdown'][data['drawdown'] == 0]
    if len(temp) < 2:
        max_period = None
    else:
        periods = (temp.index[1:].to_pydatetime() - temp.index[:-1].to_pydatetime())
        max_period = periods.max()

    return max_drawdown, max_period

if __name__ == "__main__":
    path = r'C:\market_data\USDJPY_M15.csv'
    data = generate_position(load_data(path))
    max_dd, max_dd_period = calc_drawdown(data)
    print("Max Drawdown:", max_dd)
    print("Max Drawdown Period:", max_dd_period)


#===============
#ドローダウン分析
#===============
