import ken_bot
import numpy as np
import pandas as pd
import time
import datetime
from scipy import optimize

class Kbot(ken_bot.Bot):
    def __init__(self):
        #5日間隔の移動平均
        super().__init__()
    
    def judgeForLoop(self, new_candle):
        high1 = new_candle.iloc[-2]["high"]
        high2 = new_candle.iloc[-3]["high"]
        low1 = new_candle.iloc[-2]["low"]
        low2 = new_candle.iloc[-3]["low"]
        
        long_flag1 = new_candle.iloc[-1]["close"] > high1
        long_flag2 = new_candle.iloc[-1]["close"] > high2
        short_flag1 = new_candle.iloc[-1]["close"] < low1
        short_flag2 = new_candle.iloc[-1]["close"] < low2
        
        long_flag = long_flag1 & long_flag2
        short_flag = short_flag1 & short_flag2
        
        print(high2, high1, new_candle.iloc[-1]["close"])
        print(low2, low1, new_candle.iloc[-1]["close"])
        print("long_flag:" + str(long_flag) + " short_flag:" + str(short_flag))
        
        judgement = [0, 0]
        
        if long_flag == True:
            judgement[0] = 1
        if short_flag == True:
            judgement[1] = 1
        return judgement
    
if __name__ == "__main__":
    K_bot = Kbot()
    K_bot._lot = 10
    
    
    now = datetime.datetime.now()
    
    print(now)
    
    K_bot.loop()
    
    
    