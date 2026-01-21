import pandas as pd

def load_data(path):
    raw = pd.read_csv(path)

    raw['datetime'] = pd.to_datetime(
        raw['<DTYYYYMMDD>'].astype(str) +
        raw['<TIME>'].astype(str).str.zfill(4),
        format='%Y%m%d%H%M'
    )

    raw.set_index('datetime', inplace=True)

    data = pd.DataFrame(raw['<CLOSE>'])
    data.rename(columns={'<CLOSE>': 'price'}, inplace=True)

    return data

if __name__ == "__main__":
    path = r'C:\market_data\USDJPY_M15.csv'
    data = load_data(path)
    print(data.head())


#====================================
#load_data.py（データ読み込み・前処理）
#====================================