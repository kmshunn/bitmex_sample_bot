
import bitmex_bot3
import numpy as np
import talib as ta
import time
import datetime
from scipy import optimize

class para_sar(bitmex_bot3.Bot):
    def __init__(self):
        self._iaf = 0.02
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
    #移動回帰線の追加

    def calc_moving_regression(self, baseday, time_period, df_candle_data):

        def fit_func(parameter,x,y):
            a = parameter[0]
            b = parameter[1]
            residual = y-(a*x+b)
            return residual

        day_before = baseday - datetime.timedelta(minutes=time_period-1)

        try:
            xdata = np.linspace(0, time_period - 1, num=time_period)
            time_delta_data = df_candle_data.loc[(day_before):(baseday)]
            ydata = np.array(time_delta_data["close"])
            parameter0 = [0.,0.]
            result = optimize.leastsq(fit_func, parameter0, args=(xdata,ydata))

        except:
            return np.NaN
        a_fit=result[0][0]
        b_fit=result[0][1]
 #       print(a_fit, b_fit)

        ff = a_fit*xdata+b_fit
        return ff[-1]

    def psar(self, barsdata):

        length = len(barsdata)
        high = list(barsdata['high'])
        low = list(barsdata['low'])
        close = list(barsdata['close'])
        psar = close[0:len(close)]
        psarbull = [None] * length
        psarbear = [None] * length
        bull = True

        iaf = 0.02
        maxaf = 0.2

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
    def judge(self, df_candle_stick):
        BTC_JPY_open = df_candle_stick["open"]

        df_ = df_candle_stick.reset_index()
        df_ = df_.rename(columns={"index": "date_date"})
        df_candle_stick = df_.set_index(["date_date"])

        #パラボリックSARの計算
        result = self.psar(df_)

        df_["psarbear"] = result["psarbear"]
        df_["psarbull"] = result["pearbull"]


        judgement = [[0,0,0,0] for i in range(len(df_))]

        for loop_cut in range(3, len(df_)):
            bear_sign_1 = np.isnan(df_.iloc[loop_cut]["psarbear"])
            bear_sign_2 = np.isnan(df_.iloc[loop_cut-1]["psarbear"])
            bear_sign_3 = np.isnan(df_.iloc[loop_cut-2]["psarbear"])

            bull_sign_1 = np.isnan(df_.iloc[loop_cut]["pearbull"])
            bull_sign_2 = np.isnan(df_.iloc[loop_cut-1]["pearbull"])
            bull_sign_3 = np.isnan(df_.iloc[loop_cut-2]["psarbull"])

            long_flag_1 = (~bull_sign_1) & (bull_sign_2)
            long_flag_2 = (~bull_sign_1) & (~bull_sign_2) & (bull_sign_3)

            long_flag = long_flag_1 | long_flag_2

            short_flag_1 = (~bear_sign_1) & (bear_sign_2)
            short_flag_2 = (~bear_sign_1) & (~bear_sign_2) & (bear_sign_3)

            short_flag = short_flag_1 | short_flag_2

            #ゴールデンクロス
            #ロングエントリー、ショートクローズの設定
            if long_flag:
                judgement[loop_cut][0] = BTC_JPY_open[loop_cut]
                judgement[loop_cut][3] = BTC_JPY_open[loop_cut]

            #デッドクロス
            #ショートエントリー、ロングクローズの設定
            if short_flag:
                judgement[loop_cut][1] = BTC_JPY_open[loop_cut]
                judgement[loop_cut][2] = BTC_JPY_open[loop_cut]

        return judgement

     #本番用判定ロジック(作成中)
    def judgeForLoop(self, df_candle_stick):

        df_ = df_candle_stick.reset_index()
        df_ = df_.rename(columns={'t': 'date_date'})
        #df_ = df_.rename(columns={'index': 'date_date'})

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




if __name__ == "__main__":
    para_sar_bot = para_sar()
    para_sar_bot.candleTerm = "5T"
    para_sar_bot._lot = 100
    para_sar_bot._iaf = 0.02
    para_sar_bot._af = 0.05

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

    para_sar_bot.loop()
