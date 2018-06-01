# -*- coding: utf-8 -*-

import bot_product_2
import numpy as np
import pandas as pd
import time
import datetime
from scipy import optimize

class openrange(bot_product_2.Bot):
    def __init__(self):
        #5日間隔の移動平均
        self.number = 1.4
        super().__init__()
    
    def candleDF(self, df_candle):
        df_candle1 = df_candle.reset_index()
        df_candle1.columns = ['date', 'close', 'low', 'high', 'open', 's', 'value']
        date = []
        o = []
        l = []
        h = []
        c = []
        if df_candle1.iloc[-1]["date"].hour % 2 == 0:
            for i in range(1,len(df_candle1)-1,2):
                candle1 = df_candle1.iloc[i]
                candle2 = df_candle1.iloc[i + 1]
                date.append(candle1["date"])
                o.append(candle1["open"])
                c.append(candle2["close"])
                h.append(max(candle1["high"], candle2["high"]))
                l.append(min(candle1["low"], candle2["low"]))
    
            date.append(df_candle1.iloc[-1]["date"])
            o.append(df_candle1.iloc[-1]["open"])
            c.append(df_candle1.iloc[-1]["close"])
            h.append(df_candle1.iloc[-1]["high"])
            l.append(df_candle1.iloc[-1]["low"])
            new_candle = pd.DataFrame({"date": date,
                                        "open": o,
                                        "high": h,
                                        "low": l,
                                        "close": c } )
    
    
        elif df_candle1.iloc[-1]["date"].hour % 2 == 1:
            for i in range(0,len(df_candle1),2): 
                print(i)
                candle1 = df_candle1.iloc[i]
                candle2 = df_candle1.iloc[i + 1]
                date.append(candle1["date"])
                o.append(candle1["open"])
                c.append(candle2["close"])
                h.append(max(candle1["high"], candle2["high"]))
                l.append(min(candle1["low"], candle2["low"]))
    
            new_candle = pd.DataFrame({"date": date,
                                        "open": o,
                                        "high": h,
                                        "low": l,
                                        "close": c})
    
        return new_candle


    
    def judgeForLoop(self, candle):
        new_candle = self.candleDF(candle)
        
        range_list = []
        for i in range(-2, -7, -1):
            diff = new_candle.iloc[i]["high"] - new_candle.iloc[i]["low"]
            range_list.append(diff)
            
        judgement = [0, 0]
        
        range_mean = np.array(range_list).mean()
        current_diff1 = new_candle.iloc[-1]["high"] - new_candle.iloc[-1]["open"]
        current_diff2 = new_candle.iloc[-1]["open"] - new_candle.iloc[-1]["low"]
        
        long_flag = current_diff1 > self.number * range_mean
        short_flag = current_diff2 > self.number * range_mean
        
        print(datetime.datetime.now(), new_candle.iloc[-1]["date"], new_candle.iloc[-2]["date"])
        print(range_mean)
        print("high-open: " + str(current_diff1))
        print("open-low: " + str(current_diff2))
        print("long_flag:" + str(long_flag) + " short_flag:" + str(short_flag))
    
        if long_flag == True:
            judgement[0] = 1
        if short_flag == True:
            judgement[1] = 1
        return judgement
    
if __name__ == "__main__":
    OR_bot = openrange()
    OR_bot.number = 1.4
    
    OR_bot._lot = 10
    
    now = datetime.datetime.now()
    
    print(now)
    
    OR_bot.loop()
    
    
    