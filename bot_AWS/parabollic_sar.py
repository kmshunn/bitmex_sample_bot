#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr  1 17:04:02 2018

@author: matsumototakuya
"""

import bot_aws
import numpy as np
import pandas as pd
import time
import datetime

from multiprocessing import Process

class para_sar(bot_aws.Bot):
   def __init__(self):
       self._iaf = 0.01
       self._af = 0.2
       super().__init__()

   @property
   def iaf(self):
       return self._iaf

   @iaf.setter
   def iaf(self, value):
       self._iaf = value

   @property
   def af(self):
       return self._af

   @af.setter
   def af(self, value):
       self._af = value

   def psar(self, barsdata):
        length = len(barsdata)
        high = list(barsdata['high'])
        low = list(barsdata['low'])
        close = list(barsdata['close'])
        psar = close[0:len(close)]
        psarbull = [None] * length
        psarbear = [None] * length
        bull = True
        
        iaf = self.iaf
        maxaf = self.af
        
        af = iaf
        hp = high[0]
        lp = low[0]
        
        for i in range(2,length):
            if bull:
                psar[i] = psar[i - 1] + af * (hp - psar[i - 1])
            else:
                psar[i] = psar[i - 1] + af * (lp - psar[i - 1])
            
            reverse = False
            
            if bull:
                if low[i] < psar[i]:
                    bull = False
                    reverse = True
                    psar[i] = hp
                    lp = low[i]
                    af = iaf
            else:
                if high[i] > psar[i]:
                    bull = True
                    reverse = True
                    psar[i] = lp
                    hp = high[i]
                    af = iaf
        
            if not reverse:
                if bull:
                    if high[i] > hp:
                        hp = high[i]
                        af = min(af + iaf, maxaf)
                    if low[i - 1] < psar[i]:
                        psar[i] = low[i - 1]
                    if low[i - 2] < psar[i]:
                        psar[i] = low[i - 2]
                else:
                    if low[i] < lp:
                        lp = low[i]
                        af = min(af + iaf, maxaf)
                    if high[i - 1] > psar[i]:
                        psar[i] = high[i - 1]
                    if high[i - 2] > psar[i]:
                        psar[i] = high[i - 2]
                        
            if bull:
                psarbull[i] = psar[i]
            else:
                psarbear[i] = psar[i]
    
        return { "psar":psar, "psarbear":psarbear, "psarbull":psarbull}

   #バックテスト用判定ロジック
   def judge(self,df_candle_stick):
       BTC_JPY_open = df_candle_stick["open"]

       df_ = df_candle_stick.reset_index()
       df_ = df_.rename(columns={'index': 'date_date'})
       df_candle_stick = df_.set_index(['date_date'])
       
       #パラボリックSARの計算
       result = self.psar(df_)
        
       df_["psarbear"] = result['psarbear']
       df_["psarbull"] = result['psarbull']

       
       judgement = [[0,0,0,0] for i in range(len(df_))]

       
       for loop_cnt in range(3, len(df_)):
           bear_sign_1 = np.isnan(df_.iloc[loop_cnt]["psarbear"])
           bear_sign_2 = np.isnan(df_.iloc[loop_cnt-1]["psarbear"])
           bear_sign_3 = np.isnan(df_.iloc[loop_cnt-2]["psarbear"])
           
           bull_sign_1 = np.isnan(df_.iloc[loop_cnt]["psarbull"])
           bull_sign_2 = np.isnan(df_.iloc[loop_cnt-1]["psarbull"])
           bull_sign_3 = np.isnan(df_.iloc[loop_cnt-2]["psarbull"])
           
           long_flag_1 = (~bull_sign_1) & (bull_sign_2)
           long_flag_2 = (~bull_sign_1) & (~bull_sign_2) & (bull_sign_3)
           
           long_flag = long_flag_1 | long_flag_2
           
           short_flag_1 = (~bear_sign_1) & (bear_sign_2)
           short_flag_2 = (~bear_sign_1) & (~bear_sign_2) & (bear_sign_3)
           
           short_flag = short_flag_1 | short_flag_2
           
           #ゴールデンクロス
           #ロングエントリー、ショートクローズの設定
           if long_flag:
               judgement[loop_cnt][0] = BTC_JPY_open[loop_cnt]
               judgement[loop_cnt][3] = BTC_JPY_open[loop_cnt]
#                   short_pos = 0
           #デッドクロス
           #ショートエントリー、ロングクローズの設定
           if short_flag:
               judgement[loop_cnt][1] = BTC_JPY_open[loop_cnt]
               judgement[loop_cnt][2] = BTC_JPY_open[loop_cnt]
       
       return judgement
               
   #本番用判定ロジック(作成中)  
   def judgeForLoop(self, df_candle_stick):
       
       df_ = df_candle_stick.reset_index()
       df_ = df_.rename(columns={'index': 'date_date'})
       
       #パラボリックSARの計算
       result = self.psar(df_)
        
       df_["psarbear"] = result['psarbear']
       df_["psarbull"] = result['psarbull']

       #para_sarから、ショートエントリー、ロングエントリーを判定
       judgement = [0,0,0,0]
       now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
       print(now, df_.iloc[-1]["date_date"])
       print(df_.iloc[-1]["psarbear"], df_.iloc[-2]["psarbear"], df_.iloc[-3]["psarbear"], 
             df_.iloc[-1]["psarbull"], df_.iloc[-2]["psarbull"], df_.iloc[-3]["psarbull"])
      
       bear_sign_1 = np.isnan(df_.iloc[-1]["psarbear"])
       bear_sign_2 = np.isnan(df_.iloc[-2]["psarbear"])
       bear_sign_3 = np.isnan(df_.iloc[-3]["psarbear"])
       
       bull_sign_1 = np.isnan(df_.iloc[-1]["psarbull"])
       bull_sign_2 = np.isnan(df_.iloc[-2]["psarbull"])
       bull_sign_3 = np.isnan(df_.iloc[-3]["psarbull"])
       

       
       long_flag_1 = (~bull_sign_1) & (bull_sign_2)
       long_flag_2 = (~bull_sign_1) & (~bull_sign_2) & (bull_sign_3)
       long_flag = long_flag_1 | long_flag_2
       
       short_flag_1 = (~bear_sign_1) & (bear_sign_2)
       short_flag_2 = (~bear_sign_1) & (~bear_sign_2) & (bear_sign_3)
       short_flag = short_flag_1 | short_flag_2
       
       print("long_flag:" + str(long_flag), "short_flag:" + str(short_flag))
       #ゴールデンクロス
       #ロングエントリー、ショートクローズの設定
       if long_flag:
           judgement[0] = 1
           judgement[3] = 1
#                   short_pos = 0
       #デッドクロス
       #ショートエントリー、ロングクローズの設定
       if short_flag:
           judgement[1] = 1
           judgement[2] = 1

       return judgement


def main(item):
   para_sar_bot = para_sar()

   para_sar_bot.candleTerm = "5T"
   para_sar_bot.lot = item["lot"]
   para_sar_bot.iaf = item["iaf"]
   para_sar_bot.af = item["af"]
   para_sar_bot.number = 300
   para_sar_bot.period = item["period"]
   print("iaf:" + str(para_sar_bot.iaf) + 
   ",af:" + str(para_sar_bot.af) +
   ",period:" + para_sar_bot.period + 
   ",lot:" + str(para_sar_bot.lot))
   
   para_sar_bot.judge_position()
   
   

if __name__ == '__main__':
   #稼働するボットのパラメータ設定
   #将来的には、AWS上に設置したデータベースからデータを取得して実行する想定
   dict_param = {"iaf":[0.01,0.01,0.01,0.01,0.01], 
              "af":[0.04,0.04,0.04,0.04,0.04],
              "lot":[0.01,0.01,0.01,0.01,0.01],
             "period":["300","300","300","300","300"]}

   df_param = pd.DataFrame(dict_param)
   
   #並列処理の実行
   jobs = []
   
   start_time = time.time()

   for column_name, item in df_param.iterrows():
       job = Process(target=main, args=(item, ))
       jobs.append(job)
       job.start()
   
   time.sleep(20)
   [job.join() for job in jobs]
    
   calc_time = time.time() - start_time

   print("finish, spend time:" + str(int(calc_time)))
       
