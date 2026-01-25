#「必ず1回は実行して確認するべき」  そして データが変わるたびに再確認するべき
#↓
df = pd.read_csv("price.csv")

print(df.shape) #行数・列数（shape）
print(df.head()) #中身（head）
print(df.describe()) #統計情報（describe）

# 欠損の確認
print(df.isna().sum())

# 外れ値の確認
print(df["close"].quantile([0.01, 0.99]))

#↑


#この確認も大事↓

# 連続した時間データか確認
print(df["datetime"].diff().describe())

# 価格の変化が不自然じゃないか
print(df["close"].pct_change().describe())

# 取引時間帯の偏り
print(df["datetime"].dt.hour.value_counts())

