
import bitmex_bot_RSI
import numpy as np
import pandas as pd
import talib as ta
import time
import datetime
from scipy import optimize

class rsi(bitmex_bot_RSI.Bot):
    def __init__(self):
        #rsi計算時のspan
        self.rsi_period = 14
        #何個前のRSIとのspanを取るか
        self.rsi_diff = 6
        #RSIのどんくらいの変化でオーダーを入れるか
        self.rsi = 15
        super().__init__()

    def RSI(self, df_candlestick):
        close = df_candlestick["close"]
        RSI_period = self.rsi_period
        diff = close.diff(1)
        positive = diff.clip_lower(0).ewm(alpha=1/RSI_period).mean()
        negative = diff.clip_upper(0).ewm(alpha=1/RSI_period).mean()
        RSI = 100-100/(1-positive/negative)
        RSI = pd.DataFrame(RSI).rename(columns = {"close":"RSI"})
        return RSI

    def calculate(self, df_candle):
        df_rsi = self.RSI(df_candle)
        df_candle = pd.DataFrame(df_candle["close"])
        df_candle = df_candle.join([df_rsi])

        #ローソク３個前のRSIとの差分を計算、df_candleに追加
        rsi_diff = df_rsi.diff(self.rsi_diff)
        rsi_diff = rsi_diff.rename(columns={"RSI":"rsi_diff"})
        df_candle = df_candle.join([rsi_diff])

        #同様にcloseの差分を追加
        close_diff = df_candle["close"].diff(self.rsi_diff)
        close_diff = pd.DataFrame(close_diff)
        close_diff.columns = ["close_diff"]
        df_candle = df_candle.join([close_diff])

        # top１０行を削除、インデックスをリセット
        new_candle = df_candle.iloc[10:len(df_candle)]
        new_candle = new_candle.reset_index().rename(columns = {"index":"date"})

        return new_candle

    def judgeForLoop(self, df_candlestick):

        new_candle = self.calculate(df_candlestick)

        judgement = [0,0,0,0]

        long_flag = new_candle.iloc[-2]["rsi_diff"] < -self.rsi
        short_flag = new_candle.iloc[-2]["rsi_diff"] > self.rsi
        long_c_flag = new_candle.iloc[-5]["rsi_diff"] > -self.rsi
        short_c_flag = new_candle.iloc[-5]["rsi_diff"] < self.rsi

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(now, new_candle.iloc[-2]["date"], new_candle.iloc[-8]["date"])

        print(new_candle.iloc[-2]["RSI"], new_candle.iloc[-8]["RSI"])

        print("long_flag:" + str(long_flag) + " short_flag:" + str(short_flag))

        if (long_flag == True) & (new_candle.iloc[-7]["RSI"] < 70):
            judgement[0] = 1

        if (short_flag == True) & (new_candle.iloc[-7]["RSI"] > 30):
            judgement[1] = 1

        if long_c_flag == True:
            judgement[3] == 1

        if short_c_flag == True:
            judgement[2] == 1

        return judgement



if __name__ == "__main__":
    rsi_bot = rsi()
    #rsi計算時のspan
    rsi_bot.rsi_period = 14
    #何個前のRSIとのspanを取るか
    rsi_bot.rsi_diff = 6
    #RSIのどんくらいの変化でオーダーを入れるか
    rsi_bot.rsi = 15
    rsi_bot._lot = 100

    #バックテスト用
    #para_sar_bot.describeResult(candleTerm=para_sar_bot.candleTerm, cost=para_sar_bot.cost)
    #本番用（実行時にはコメントアウトを解除すること）
    #開始時間まで待つ
    now = datetime.datetime.now()
    print(now.strftime("%Y-%m-%d %H:%M:%S"))
    start_time = now + datetime.timedelta(minutes=1)
    start_time = start_time.replace(second=15, microsecond=0)
    time_diff = int((start_time - now).total_seconds())
    print("Waiting...")
    time.sleep(time_diff)
    print("start time:" + now.strftime("%Y-%m-%d %H:%M:%S"))
    time.sleep(30)

    rsi_bot.loop()
