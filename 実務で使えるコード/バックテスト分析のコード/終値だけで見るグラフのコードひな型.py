# -*- coding: utf-8 -*-
import pandas as pd
import matplotlib.pyplot as plt

# ===============================
# CSVファイル読み込み
# ===============================
file_path = r"C:\Users\Ryouh\OneDrive\デスクトップ\VScode用データ\実務で使えるコード\バックテスト分析のコード\USDJPY_M5.csv"
df = pd.read_csv(file_path)

# 列名の前後空白を削除（念のため）
df.columns = df.columns.str.strip()

# <TIME> 列を文字列に変換して4桁に揃える
df['TIME_str'] = df['<TIME>'].astype(str).str.zfill(4)

# <DTYYYYMMDD> と TIME_str を結合して datetime 型に変換
df['datetime'] = pd.to_datetime(
    df['<DTYYYYMMDD>'].astype(str) + df['TIME_str'],
    format='%Y%m%d%H%M'
)

# datetime をインデックスに設定（横軸を時間にする）
df = df.set_index('datetime')

# 終値の列名を "close" に変更
df = df.rename(columns={"<CLOSE>": "close"})

# ===============================
# 終値の折れ線グラフを描画
# ===============================
plt.figure(figsize=(12,5))        # グラフサイズを指定
df['close'].plot()                 # 終値をプロット
plt.title("USDJPY Close Price")   # グラフタイトル
plt.xlabel("Date")                # X軸ラベル
plt.ylabel("Price")               # Y軸ラベル
plt.grid(True)                    # グリッド表示
plt.show()                        # グラフ表示



#=================
#グラフとしての意味
#=================
#「終値の値動きそのままの折れ線グラフ」
#これだけでも トレンドの方向、上昇／下降、レンジ相場 が一目でわかる
#後から 移動平均線（MA）やシグナル を重ねることで、裁量やバックテストに活かせる

#応用も簡単 → ここに MA やシグナル列を足せば、すぐにバックテストグラフ化できる