#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 31 16:32:09 2018

@author: matsumototakuya
"""
#テクニカル系botの基底クラス．ローソク足でのバックテスト．注文処理を実装．
import pybitflyer
import sys
import json
import csv
import math
import pandas as pd
import time
import requests
import datetime

class Order:
   def __init__(self, key, secret):
       self.product_code = "FX_BTC_JPY"
       self.key = key
       self.secret = secret
       self.api = pybitflyer.API(self.key, self.secret)
       #最新の注文リスト
       self.latest_exec_info = []

   def limit(self, side, price, size, minute_to_expire=None):
       print("Order: Limit. Side : {}".format(side))
       response = {"status":"internalError in order.py"}
       try:
           response = self.api.sendchildorder(product_code=self.product_code, child_order_type="LIMIT", side=side, price=price, size=size, minute_to_expire = minute_to_expire)
       except:
           pass
       while "status" in response:
           try:
               response = self.api.sendchildorder(product_code=self.product_code, child_order_type="LIMIT", side=side, price=price, size=size, minute_to_expire = minute_to_expire)
           except:
               pass
           time.sleep(3)
       return response

   def market(self, side, size, minute_to_expire= None):
       print("Order: Market. Side : {}".format(side))
       response = {"status": "internalError in order.py"}
       try:
           response = self.api.sendchildorder(product_code=self.product_code, child_order_type="MARKET", side=side, size=size, minute_to_expire = minute_to_expire)
           print(response)
       except:
           pass
       while "status" in response:
           try:
               response = self.api.sendchildorder(product_code=self.product_code, child_order_type="MARKET", side=side, size=size, minute_to_expire = minute_to_expire)
               print(response)
           except:
               pass
           time.sleep(3)
       return response

   def stop(self, side, size, trigger_price, minute_to_expire=None):
       print("Order: Stop. Side : {}".format(side))
       response = {"status": "internalError in order.py"}
       try:
           response = self.api.sendparentorder(order_method="SIMPLE", parameters=[{"product_code": self.product_code, "condition_type": "STOP", "side": side, "size": size,"trigger_price": trigger_price, "minute_to_expire": minute_to_expire}])
       except:
           pass
       while "status" in response:
           try:
               response = self.api.sendparentorder(order_method="SIMPLE", parameters=[{"product_code": self.product_code, "condition_type": "STOP", "side": side, "size": size,"trigger_price": trigger_price, "minute_to_expire": minute_to_expire}])
           except:
               pass
           time.sleep(3)
       return response

   def stop_limit(self, side, size, trigger_price, price, minute_to_expire=None):
       print("Side : {}".format(side))
       response = {"status": "internalError in order.py"}
       try:
           response = self.api.sendparentorder(order_method="SIMPLE", parameters=[{"product_code": self.product_code, "condition_type": "STOP_LIMIT", "side": side, "size": size,"trigger_price": trigger_price, "price": price, "minute_to_expire": minute_to_expire}])
       except:
           pass
       while "status" in response:
           try:
               response = self.api.sendparentorder(order_method="SIMPLE", parameters=[{"product_code": self.product_code, "condition_type": "STOP_LIMIT", "side": side, "size": size,"trigger_price": trigger_price, "price": price, "minute_to_expire": minute_to_expire}])
           except:
               pass
       return response

   def trailing(self, side, size, offset, minute_to_expire=None):
       print("Side : {}".format(side))
       response = {"status": "internalError in order.py"}
       try:
           response = self.api.sendparentorder(order_method="SIMPLE", parameters=[{"product_code": self.product_code, "condition_type": "TRAIL", "side": side, "size": size, "offset": offset, "minute_to_expire": minute_to_expire}])
       except:
           pass
       while "status" in response:
           try:
               response = self.api.sendparentorder(order_method="SIMPLE", parameters=[{"product_code": self.product_code, "condition_type": "TRAIL", "side": side, "size": size, "offset": offset, "minute_to_expire": minute_to_expire}])
           except:
               pass
       return response
       

   
   """
   現状のポジションをチェック
   """
   def check_current_position(self):
       position_list = self.api.getpositions(product_code="FX_BTC_JPY")
       df_position_list = pd.DataFrame(position_list)
       
       pos = 0
       
       if len(df_position_list) > 0:
           side_ = df_position_list.iloc[0]["side"]
           if side_ == "BUY":
               pos = 1
           else:
               pos = -1
       else:
           pos=0
           
       return pos           
       
   """
   現状のポジションの損益を送付する
   """
   def get_pos_info(self):
       position_list = self.api.getpositions(product_code="FX_BTC_JPY")
       df_position_list = pd.DataFrame(position_list)
       
       message = "SIDE:" +  df_position_list.iloc[0]["side"] + ", PRICE:" + str(df_position_list["price"].mean()) + ", PL:" + str(df_position_list["pnl"].sum())
       return message
   """
   ポジションをクローズするタイミングで収支を計算して、CSVに保存する
   
   """
   def calc_profitloss(self):
       #最新の約定情報を取得
       execution_hist = self.api.getexecutions(product_code="FX_BTC_JPY")
       df_execution_hist= pd.DataFrame(execution_hist)
       
       #直近のポジションと結合するため、キーの名前を変更
       df_execution_hist = df_execution_hist.rename(columns={'exec_date': 'key1', 'side':'key2', 'size':'key3'})
       
       #現在のポジションを取得
       position_list = self.api.getpositions(product_code="FX_BTC_JPY")
       df_position_list = pd.DataFrame(position_list)
       
       #直近の約定情報と結合するため、キーの名前を変更
       df_position_list = df_position_list.rename(columns={'open_date': 'key1', 'side':'key2', 'size':'key3'})

       #約定情報とポジションをマージ
       df_list = pd.merge(df_execution_hist, df_position_list, on=['key1', 'key2','key3'])
       #重複行を削除
       df_list = df_list.drop_duplicates(subset=['id'])
       #カラムをリネームし、クローズした時刻を追加
       df_list = df_list.rename(columns={'key1': 'open_date', 'key2':'side', 'key3':'size'})
       df_list["close_date"] = datetime.datetime.now() - datetime.timedelta(hours=9)
       #現在時刻取得
       current_time = datetime.datetime.now().strftime('%m%d%H%M%S')
       # #取得結果をCSVに保存
       file_name = "./exec_info_" + current_time + ".csv"
       df_list.to_csv(file_name, index=False, encoding='UTF-8_sig')

       return       


class Bot:
   def __init__(self):
       #pubnubから取得した約定履歴を保存するリスト
       self._lot = 0.1
       self._product_code = "FX_BTC_JPY"
       #何分足のデータを使うか．初期値は1分足．
       self._candleTerm = "1T"
       self._period = "60"
       self._number = 300
       
       
       #現在のポジション．1ならロング．-1ならショート．0ならポジションなし．
       self._pos = 0
       #onplanetz API key
       key = "Qw2S5685vueFFoUaGfeCcu"
       secret = "VKXc/Zwdx+38OTxtqpxaV6VUev5QCzIBe73fhjHSDWM="
       self.order = Order(key, secret)
       self.next_order_min = datetime.datetime.now()
       self.api = pybitflyer.API(key, secret)

       #ラインに稼働状況を通知
       self.line_notify_token = 'CHVGTfW9xeT3dPTTgJgMuhM5pBFQr2aZljEdlxw1rqY'
       self.line_notify_api = 'https://notify-api.line.me/api/notify'
       #証拠金
       self._margin = self.api.getcollateral()
       #注文執行コスト
       self._cost = 0

   @property
   def cost(self):
       return self._cost

   @cost.setter
   def cost(self, value):
       self._cost = value

   @property
   def margin(self):
       return self._margin
   @margin.setter
   def margin(self, val):
       self._margin = val
   @property
   def candleTerm(self):
       return self._candleTerm
   @candleTerm.setter
   def candleTerm(self, val):
       """
       valは"5T"，"1H"などのString
       """
       self._candleTerm = val
   @property
   def executions(self):
       return self._executions
   @executions.setter
   def executions(self, val):
       self._executions = val
   @property
   def pos(self):
       return self._pos
   @pos.setter
   def pos(self, val):
       self.pos = int(val)
   @property
   def lot(self):
       return self._lot
   @lot.setter
   def lot(self, val):
       self._lot = round(val,3)
   @property
   def product_code(self):
       return self._product_code
   @product_code.setter
   def product_code(self, val):
       self._product_code = val
   @property
   def period(self):
       return self._period
   @period.setter
   def period(self, val):
       self._period = val
   @property
   def number(self):
       return self._number
   @number.setter
   def number(self, val):
       self._number = val

   def calculateLot(self, margin):
       """
       証拠金からロットを計算する関数．
       """
       lot = math.floor(margin*10**(-4))*10**(-2)
       return round(lot,2)
       
   
   
   def judge(self, df_candleStick):
       """
       バックテスト用の売り買い判断を行う関数．judgementリストは[買いエントリー，売りエントリー，買いクローズ（売り），売りクローズ（買い）]のリスト(つまり「二次元リスト)になっている．リスト内リストの要素は，0（シグナルなし）,シグナル点灯時価格（シグナル点灯時のみ）を取る．
       if Trueの部分にシグナル点灯条件を入れる．
       """
       judgement = [[0,0,0,0] for i in range(len(df_candleStick.index))]

       for i in range(len(df_candleStick.index)):
           #ロングエントリー
           if True:
               judgement[i][0] = 1
           #ショートエントリー
           if True:
               judgement[i][1] = 1
           #ロングクローズ
           if True:
               judgement[i][2] = 1
           #ショートクローズ
           if True:
               judgement[i][3] = 1
       return judgement

   def judgeForLoop(self):
       """
       実働時用の売り買い判断．judgementリストは[買いエントリー，売りエントリー，買いクローズ（売り），売りクローズ（買い）]のリストになっている．（値は0or1）
       実際の関数は、各ロジックのpythonコードに記載
       """
       judgement = [0,0,0,0]
       #ロングエントリー
       if True:
           judgement[0] = 1
       #ショートエントリー
       if True:
           judgement[1] = 1
       #ロングクローズ
       if True:
           judgement[2] = 1
       #ショートクローズ
       if True:
           judgement[3] = 1
       return judgement


   def getCandlestick(self, number, period):
       """
       number:ローソク足の数．period:ローソク足の期間（文字列で秒数を指定，Ex:1分足なら"60"）．cryptowatchはときどきおかしなデータ（price=0）が含まれるのでそれを除く．
       """
       #ローソク足の時間を指定
       periods = [period]
       #クエリパラメータを指定
       query = {"periods":','.join(periods)}
       #ローソク足取得
       res = json.loads(requests.get("https://api.cryptowat.ch/markets/bitflyer/btcfxjpy/ohlc",params=query).text)["result"]
       #ローソク足のデータを入れる配列．
       data = []
       for i in periods:
           row = res[i]
           length = len(row)
           for column in row[:length-(number+1):-1]:
               #dataへローソク足データを追加．
               if column[4] != 0:
                   column = column[0:6]
                   data.append(column)
       return data[::-1]

   def fromListToDF(self, candleStick):
       """
       Listのローソク足をpandasデータフレームへ．
       """
       date = [price[0] for price in candleStick]
       priceOpen = [int(price[1]) for price in candleStick]
       priceHigh = [int(price[2]) for price in candleStick]
       priceLow = [int(price[3]) for price in candleStick]
       priceClose = [int(price[4]) for price in candleStick]
       date_datetime = map(datetime.datetime.fromtimestamp, date)
       dti = pd.DatetimeIndex(date_datetime)
       df_candleStick = pd.DataFrame({"open" : priceOpen, "high" : priceHigh, "low": priceLow, "close" : priceClose}, index=dti)
       return df_candleStick

   def processCandleStick(self, candleStick, timeScale):
       """
       1分足データから各時間軸のデータを作成.timeScaleには5T（5分），H（1時間）などの文字列を入れる
       """
       df_candleStick = self.fromListToDF(candleStick)
       processed_candleStick = df_candleStick.resample(timeScale).agg({'open': 'first','high':'max','low': 'min','close': 'last'})
       processed_candleStick = processed_candleStick.dropna()
       return processed_candleStick

   def lineNotify(self, message, fileName=None):
       """
       Lineに通知を送信．
       画像ファイルの有無で処理を分ける
       """
       payload = {'message': message}
       headers = {'Authorization': 'Bearer ' + self.line_notify_token}
       if fileName == None:
           try:
               requests.post(self.line_notify_api, data=payload, headers=headers)
           except:
               pass
       else:
           try:
               files = {"imageFile": open(fileName, "rb")}
               requests.post(self.line_notify_api, data=payload, headers=headers, files = files)
           except:
               pass

   def describePLForNotification(self, pl, df_candleStick):
       """
       LineNotifyに損益グラフを送るための関数．
       """
       import matplotlib
       matplotlib.use('Agg')
       import matplotlib.pyplot as plt
       close = df_candleStick["close"]
       index = range(len(pl))
       # figure
       fig = plt.figure(figsize=(20,12))
       #for price
       ax = fig.add_subplot(2, 1, 1)
       ax.plot(df_candleStick.index, close)
       ax.set_xlabel('Time')
       # y axis
       ax.set_ylabel('The price[JPY]')
       #for PLcurve
       ax = fig.add_subplot(2, 1, 2)
       # plot
       ax.plot(index, pl, color='b', label='The PL curve')
       # x axis
       ax.set_xlabel('The number of Trade')
       # y axis
       ax.set_ylabel('The estimated Profit/Loss(JPY)')
       # legend and title
       ax.legend(loc='best')
       ax.set_title('The PL curve(Time span:{})'.format(self.candleTerm))
       # save as png
       today = datetime.datetime.now().strftime('%Y%m%d')
       number = "_" + str(len(pl))
       fileName = today + number + ".png"
       plt.savefig(fileName)
       plt.close()
       return fileName

   def judge_position(self,candleTerm=None, period=None):
       """
       過去の価格から、テクニカル指標を計算し、取るべきポジションを判定
       価格情報を取得する箇所以降は各ボットごとに実行するため、非同期処理で行う
       """
       try:
           pl = []
           pl.append(0)
           lastPositionPrice = 0
           lot = self.lot
           print("trading lot:" + str(lot))
           try:
               pos = self.order.check_current_position()
               print("current position:" + str(pos))
           except:
               print("Unknown error happend when you check current position")
           finally:
               pass
           
           try:
               candleStick = self.getCandlestick(self.number, self.period)
           except:
               print("Unknown error happend when you requested candleStick")
           finally:
               pass
           
           if candleTerm == None:
               df_candleStick = self.fromListToDF(candleStick)
           else:
               df_candleStick = self.processCandleStick(candleStick, candleTerm)

           judgement = self.judgeForLoop(df_candleStick)
           try :
               ticker = self.api.ticker(product_code=self.product_code)
           except:
               print("Unknown error happend when you requested ticker.")
           finally:
               pass

           best_ask = ticker["best_ask"]
           best_bid = ticker["best_bid"]


           #現在のpositionチェック開始までの時間
           next_order_span = 10
           message = ""
           #ここからエントリー，クローズ処理
           if pos == 0:
               #ロングエントリー
               #現在のpositionをチェックし、既に存在する場合はpositionをセットする
               try:
                   position_list = self.order.api.getpositions(product_code="FX_BTC_JPY")
                   df_position_list = pd.DataFrame(position_list)
                   
                   if len(df_position_list) > 0:
                       side_ = df_position_list.iloc[0]["side"]
                       if side_ == "BUY":
                           message = "long position already exist"
                           self.lineNotify(message)
                           pos += 1
                       else:
                           message = "short position already exist"
                           self.lineNotify(message)                           
                           pos -= 1
               except:
                   pass
               
               if judgement[0]:
                   self.next_order_min = datetime.datetime.now() + datetime.timedelta(minutes=next_order_span)
                   print(datetime.datetime.now(), self.next_order_min)
                   self.order.market(size=lot, side="BUY")
                   pos += 1
                   message = "Long entry. Lot:{}, Price:{}".format(lot, best_ask)
                   self.lineNotify(message)
                   
                   lastPositionPrice = best_ask
               #ショートエントリー
               elif judgement[1]:
                   self.next_order_min = datetime.datetime.now() + datetime.timedelta(minutes=next_order_span)
                   print(datetime.datetime.now(), self.next_order_min)
                   self.order.market(size=lot,side="SELL")
                   pos -= 1
                   message = "Short entry. Lot:{}, Price:{}, ".format(lot, best_bid)
                   self.lineNotify(message)
                   
                   lastPositionPrice = best_bid
           elif pos == 1:
               #ロングクローズ
              
               time_diff = self.next_order_min - datetime.datetime.now()
               if time_diff.total_seconds()  < 0:
                    #現在のpositionをチェック
                   try:
                       position_list = self.order.api.getpositions(product_code="FX_BTC_JPY")
                       df_position_list = pd.DataFrame(position_list)
                       
                       if len(df_position_list) == 0:
                           #既にクローズされていている場合
                           message = "long position closed manually, currently no position"
                           self.lineNotify(message)
                           pos -= 1
                       else:
                           #既にクローズされていて、かつショートのエントリーがある場合
                           side_ = df_position_list.iloc[0]["side"]
                           if side_ == "SELL":
                               message = "long position closed and short position entry manually, currently short position"
                               self.lineNotify(message)
                               pos -= 2
                   except:
                       #exception発生時はpass(ネットワークエラー発生のため)
                       pass
                      
               if judgement[2]:
                   #クローズ前に直近の損益情報を保存し、csv出力
                   try:
                      self.order.calc_profitloss()
                   except:
                       pass
                   
                   self.next_order_min = datetime.datetime.now() + datetime.timedelta(minutes=next_order_span)
                   print(datetime.datetime.now(), self.next_order_min)
                   self.order.market(size=lot,side="SELL")
                   pos -= 1
                   plRange = best_bid - lastPositionPrice
                   pl.append(pl[-1] + plRange * lot)

                   message = "Long close. Lot:{}, Price:{}, pl:{}".format(lot, best_bid, pl[-1])
                   print(message)
                   
#                   fileName = self.describePLForNotification(pl, df_candleStick)
                   self.lineNotify(message)
           elif pos == -1:
               #ショートクローズ
               time_diff = self.next_order_min - datetime.datetime.now()
               if time_diff.total_seconds()  < 0:
               #現在のpositionをチェック
                   try:
                       position_list = self.order.api.getpositions(product_code="FX_BTC_JPY")
                       df_position_list = pd.DataFrame(position_list)
                       #既にクローズされている場合
                       if len(df_position_list) == 0:
                           message = "short position closed manually, currently no position"
                           self.lineNotify(message)
                           pos += 1
                       else:
                           #既にクローズされていて、かつロングのエントリーがある場合
                           side_ = df_position_list.iloc[0]["side"]
                           if side_ == "BUY":
                               message = "short position closed and long position entry manually, currently long position"
                               self.lineNotify(message)
                               pos += 2
                   except:
                       #exception発生時はpass(ネットワークエラー発生のため)
                       pass
               
               if judgement[3]:
                   #クローズ前に直近の損益情報を保存し、csv出力
                   try:
                      self.order.calc_profitloss()
                   except:
                       pass
                   self.next_order_min = datetime.datetime.now() + datetime.timedelta(minutes=next_order_span)
                   print(datetime.datetime.now(), self.next_order_min)
                   self.order.market(size=lot, side="BUY")
                   pos += 1
                   plRange = lastPositionPrice - best_ask
                   pl.append(pl[-1] + plRange * lot)
                   #ラインに通知
                   message = "Short close. Lot:{}, Price:{}, pl:{}".format(lot, best_ask, pl[-1])
                   print(message)
#                   fileName = self.describePLForNotification(pl, df_candleStick)
                   self.lineNotify(message)
                   
#           さらに，クローズと同時にエントリーシグナルが出ていたときの処理．
           if pos == 0:
               #ロングエントリー
               if judgement[0]:
                   print(datetime.datetime.now())
                   self.next_order_min = datetime.datetime.now() + datetime.timedelta(minutes=next_order_span)
                   self.order.market(size=lot, side="BUY")
                   pos += 1
                   message = "Long entry. Lot:{}, Price:{}".format(lot, best_ask)
                   self.lineNotify(message)
                   lastPositionPrice = best_ask
               #ショートエントリー
               elif judgement[1]:
                   print(datetime.datetime.now())
                   self.next_order_min = datetime.datetime.now() + datetime.timedelta(minutes=next_order_span)
                   self.order.market(size=lot,side="SELL")
                   pos -= 1
                   message = "Short entry. Lot:{}, Price:{}".format(lot, best_bid)
                   self.lineNotify(message)
                   lastPositionPrice = best_bid
                   
           try:
               message = self.order.get_pos_info()
           except:
#               print("error")
               message = "Waiting."
               pass
           #5分ごとに通知
           if datetime.datetime.now().minute % 5 == 0 and datetime.datetime.now().second < 30:
               print(message)
               self.lineNotify(message)
       except:
           print("Unknown error happend")
           
if __name__ == '__main__':
   pass
