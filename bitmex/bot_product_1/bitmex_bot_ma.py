import time
from time import sleep
import json
import ccxt
import requests
import datetime
import pandas as pd


class order():
    def __init__(self, key, secret):
        self.product_code = 'BTC/USD'
        self.key = key
        self.secret = secret
        self.api = ccxt.bitmex({
        'apiKey' : key,
        'secret' : secret
        })
        self.api.urls['api'] = self.api.urls['test']
        #最新の注文リスト
        self.api.fetch_order_book (self.product_code)

    def limit(self, side, price, size):
        print("Order: Limit. side: {} size: {} price:{}".format(side, size, price))
        response = {"error":"internalError in order.py"}
        try:
            response = self.api.create_order(self.product_code, type="limit", side=side, price=price, amount=size)
        except:
            pass
        while "error" in response:
            try:
                response = self.api.create_order(self.product_code, type="limit", side=side, price=price, amount=size)
            except:
                pass
            time.sleep(3)
        return response

    def market(self, side, size):
        print("Order: Market. side: {} size: {}".format(side, size))
        response = {"status":"internalError in order.py"}
        #self.api.create_order(self.product_code, type="market", side=side, amount=size)
        try:
            response = self.api.create_order(self.product_code, type="market", side=side, amount=size)
        except:
            pass
        print(response)
        while "status" in response:
            try:
                response = self.api.create_order(self.product_code, type="market", side=side, amount=size)
            except:
                pass
            time.sleep(60)
        return response


    def get_pos_info(self):
        position_list = self.api.private_get_position()[1]
        if position_list['currentQty'] == 0: # sizeが0より大きければ現在LONG状態、0より小さければ現在SHORT状態と判断
            side = 'NO POSITION'
        elif position_list['currentQty'] > 0:
            side = 'LONG'
        else:
            side = 'SHORT'
        message = "Side:" + side + ", Size:" + str(round(position_list['currentQty'])) + ", avgEntryPrice:" + str(position_list['avgEntryPrice'])
        return message


class Bot:
    def __init__(self):
        #pubnubから取得した約定履歴を保存するリスト
        #self._executions = deque(maxlen=300)
        self._lot = 0.1
        self._product_code = 'BTC/USD'
        #何分足のデータを使うか．初期値は1分足．
        self._candleTerm = "1T"
        #現在のポジション．1ならロング．-1ならショート．0ならポジションなし．
        self._pos = 0
        #API key(自分のキーに書き換える)
        key = "VHppd1wDBRP3gAcyFGnb1A6f"
        secret = "ESffLhyr1SSum1mQ-fiRTlNaK8wtAujeP-MFXLaFYzXimch3"
        self.order = order(key, secret)
        self.next_order_min = datetime.datetime.now()
        self.api = ccxt.bitmex({
        'apiKey' : key,
        'secret' : secret
        })
        self.api.urls['api'] = self.api.urls['test']

        #ラインに稼働状況を通知(トークンのキーは適宜書き換える)
        self.line_notify_token = 'fVXGnTYKe6uORVNOJJzwbpqzUwTpPr01YZWkq3H1X7o'
        self.line_notify_api = 'https://notify-api.line.me/api/notify'
        #証拠金
        #self._margin = self.api.getcollateral()
        #注文執行コスト
        self._cost = 0

    def getCandlestick(self, number, period):
        """
        number:ローソク足の数．period:ローソク足の期間（文字列で秒数を指定，Ex:1分足なら"60"）．cryptowatchはときどきおか
        しなデータ（price=0）が含まれるのでそれを除く．
        """

        now = datetime.datetime.now().strftime('%s') # 現在時刻の取得
        r = requests.get('https://testnet.bitmex.com/api/udf/history?symbol=XBTUSD&resolution=' + str(int(period)/60) + '&from=' +
        str(int(now)-int(period)*(number-1)) + '&to=' + now)
        ohlcv = r.json()
        df_ = pd.DataFrame(ohlcv)
        df_ = df_.rename(columns = {"c":"close", "h":"high", "l":"low", "o":"open", "t":"index", "v":"value"})
        df_ = df_[["index", "close", "low",  "high", "open", "s", "value"]]

        time_date = []
        for i in df_.iloc[:,0]:
             time = datetime.datetime.fromtimestamp(i)
             time_date.append(time)
        dti = pd.DatetimeIndex(time_date)
        df_["index"] = dti
        df_ = df_.set_index("index")
        return df_


    def loop(self, candleterm=None):
        """
        注文の実行ループを回す関数
        """

        try:
            position_list = self.api.private_get_position()[1]

            if position_list['currentQty'] == 0:
                pos = 0
            elif position_list['currentQty'] > 0:
                pos = 1
            else:
                pos = -1

        except:
            #exception発生時はpass(ネットワークエラー発生のため)
            pass

        pl = []
        pl.append(0)
        lastPositionPrice = 0
        lot = self._lot
        print(lot)
        while True:
            try:
                df5 = self.getCandlestick(30, "300")
                df24 = self.getCandlestick(30, "86400")
            except:
                print("Unknown error happened when you requested candle stick")
            finally:
                pass

            judgement = self.judgeForLoop(df5, df24)
            try:
                ticker = self.api.fetch_ticker(self._product_code)
            except:
                print("Unknown error happened when you requested ticker.")
            finally:
                pass

            #指値で注文したい場合に求める
            #best_ask = ticker["best_ask"]
            #best_bid = ticker["best_bid"]
            Bid = ticker["bid"]
            Ask = ticker["ask"]
            Price = ticker["close"]

            #前回取引してから５分以上経過していない場合は、ポジションを変更しない
            next_order_span = 5

            message = ""

            #ここからエントリー、クローズ処理
            if pos == 0:
                #ロングエントリー
                if judgement[0] == 1:
                    print(datetime.datetime.now())
                    order = self.order.market("buy", lot)
                    pos += 1
                    message = "Long entry. size:{}, price:{}".format(lot, order["price"])
                    print(message)

                    lastPositionPrice = order["price"]
                #ショートエントリー
                elif judgement[1] == 1 :
                    print(datetime.datetime.now())
                    order = self.order.market("sell", lot)
                    pos -= 1
                    message = "Short entry. size:{}, price:{}".format(lot, order["price"])
                    print(message)

                    lastPositionPrice = order["price"]

            elif pos == 1:
                #ロングクローズ
                #現在のポジションをチェックし、存在しない場合はpositionを０にする
                try:
                    position_list = self.api.private_get_position()[1]

                    if position_list['currentQty'] == 0:
                        message = "Long position closed manually, currently no position."
                        print(message)
                        pos -= 1

                except:
                    #exception発生時はpass(ネットワークエラー発生のため)
                    pass
                
                try:
                    total = self.api.fetch_balance()["BTC"]["total"]
                    entry_price = position_list["avgEntryPrice"]
                    current_price = Price
                    profit = (current_price - entry_price)/entry_price * lot/entry_price
                    
                    if abs(profit) > total*0.01:
                        order = self.order.market("sell", lot)
                        message = "Long close. size:{}, price:{}".format(lot, order["price"])
                except:
                    pass
                        

            elif pos == -1:
                #ショートクローズ
                #現在のpositionをチェックし、存在しない場合はpositionをゼロにする
                try:
                    position_list = self.api.private_get_position()[1]

                    if position_list['currentQty'] == 0:
                        message = "short position closed manually, currently no position"
                        print("message")
                        pos += 1
                except:
                    #exception発生時はpass(ネットワークエラー発生のため)
                    pass
                
                try:
                    total = self.api.fetch_balance()["BTC"]["total"]
                    entry_price = position_list["avgEntryPrice"]
                    current_price = Price
                    profit = (current_price - entry_price)/entry_price * lot/entry_price
                    
                    if abs(profit) > total*0.01:
                        order = self.order.market("buy", lot)
                        message = "Long close. size:{}, price:{}".format(lot, order["price"])
                except:
                    pass
                
            

            #さらに，クローズと同時にエントリーシグナルが出ていたときの処理．
            if pos == 0:
                #ロングエントリー
                if judgement[0] == 1:
                    print(datetime.datetime.now())
                    order = self.order.market("buy", lot)
                    pos += 1
                    message = "Long entry. size:{}, price:{}".format(lot, order["price"])
                    print(message)

                    lastPositionPrice = order["price"]
                #ショートエントリー
                elif judgement[1] == 1 :
                    print(datetime.datetime.now())
                    order = self.order.market("sell", lot)
                    pos -= 1
                    message = "Short entry. size:{}, price:{}".format(lot, order["price"])
                    print(message)

                    lastPositionPrice = order["price"]



            time.sleep(30)
            try:
                message = self.order.get_pos_info()
            except:
                message = "Waiting."
                pass

            if datetime.datetime.now().minute % 5 == 0 and datetime.datetime.now().second < 30:
                print(message)
                print(pos)


if __name__ == '__main__':
   pass
