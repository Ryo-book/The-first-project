import pandas as pd

file_path = r"C:\market_data\USDJPY_M5.csv"

df = pd.read_csv(file_path)
print(df.columns)