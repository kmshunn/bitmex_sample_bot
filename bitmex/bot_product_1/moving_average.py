import bitmex_bot_ma
import numpy as np
import pandas as pd
import time
import datetime
from scipy import optimize

class moving_average(bitmex_bot_ma.Bot):
    def __init__(self):
        #5日間隔の移動平均
        self.MA_period = 5
        super().__init__()
    
    def calculate(self, df24):
        df24_close = pd.DataFrame(df24["close"])
        MA_period = 5
        SMA = df24_close.rolling(MA_period).mean()
        df24_close["SMA"] = SMA
        df24_close = df24_close.iloc[5:len(df24_close)]
        return df24_close
    
    def judgeForLoop(self, df5, df24):
        df24_close = self.calculate(df24)
        df5_close = pd.DataFrame(df5["close"])
        
        judgement = [0, 0]
        
        long_flag = (df5_close.iloc[-3]["close"] < df24_close.iloc[-1]["SMA"]) & (df5_close.iloc[-2]["close"] > df24_close.iloc[-1]["SMA"]) & (df5_close.iloc[-1]["close"] > df24_close.iloc[-1]["SMA"])
        short_flag = (df5_close.iloc[-3]["close"] > df24_close.iloc[-1]["SMA"]) & (df5_close.iloc[-2]["close"] < df24_close.iloc[-1]["SMA"]) & (df5_close.iloc[-1]["close"] < df24_close.iloc[-1]["SMA"])
        
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(now, df5_close.iloc[-3].name, df5_close.iloc[-2].name, df5_close.iloc[-1].name)
        print(str(df5_close.iloc[-3]["close"]) + ":" + str(df24_close.iloc[-1]["SMA"]))
        print(str(df5_close.iloc[-2]["close"]) + ":" + str(df24_close.iloc[-1]["SMA"]))
        print(str(df5_close.iloc[-1]["close"]) + ":" + str(df24_close.iloc[-1]["SMA"]))
        print("long_flag:" + str(long_flag) + " short_flag:" + str(short_flag))
        
        if long_flag == True:
            judgement[0] = 1
        
        if short_flag == True:
            judgement[1] = 1
        
        return judgement
    
if __name__ == "__main__":
    MA_bot = moving_average()
    MA_bot._lot = 0.1
    
    MA_bot.MA_period = 5
    
    now = datetime.datetime.now()
    
    print(now)
    
    MA_bot.loop()
    
    
    