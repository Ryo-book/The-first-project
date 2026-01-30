import pandas as pd
import numpy as np

# =========================
# ①データ読み込み
# =========================
def load_data(path):
    df = pd.read_csv(path) #ここにCSVデータをのせる
    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time").set_index("time")
    return df


# =========================
# ②インジケータ計算
# =========================
def add_indicators(df, ma_period=20):
    df["ma"] = df["close"].rolling(ma_period).mean()
    df["trend"] = df["close"] > df["ma"]
    return df


# =========================
# ③エントリー条件
# =========================
def generate_signal(df):
    df["entry"] = df["trend"] & (~df["trend"].shift(1))
    return df


# =========================
# ④バックテスト本体
# =========================
def backtest(df, hold_bars=5):
    df["profit"] = np.where(
        df["entry"],
        df["close"].shift(-hold_bars) - df["close"],
        0
    )
    return df


# =========================
# ⑤成績集計
# =========================
def summarize(df):
    return {
        "trades": int(df["entry"].sum()),
        "total_profit": df["profit"].sum(),
        "win_rate": (df["profit"] > 0).mean()
    }


# =========================
# ⑥実行部分（ここが重要）
# =========================
if __name__ == "__main__":  #ここにCSVをのせることで、このファイルを直接実行した時だけ動くようにできる。
    df = load_data("USDJPY.csv")
    df = add_indicators(df, ma_period=20)
    df = generate_signal(df)
    df = backtest(df, hold_bars=5)

    stats = summarize(df)
    print(stats)


#if __name__ == "__main__":　←　これがあるから
#importしてもバックテストが走らない、戦略ライブラリ化できる、EA化・最適化にもつなげられる

#==========================


#=====================================================================
#これは、バックテストコードを量産するための“基礎ひな型”
#[ひな型として優秀な理由]
#① 構造が固定されている

#どの戦略でも流れは同じ：

#データ読み込み、指標計算、シグナル生成、バックテスト、成績集計、実行ガード
#👉 ロジックが変わっても骨格は不変
#👉 思考コストが下がる
#=====================================================================

