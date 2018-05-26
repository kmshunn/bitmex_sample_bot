import ccxt
import pandas as pd
import datetime
import requests

def a(number, period):
    now = datetime.datetime.now().strftime('%s') # 現在時刻の取得
    r = requests.get('https://testnet.bitmex.com/api/udf/history?symbol=XBTUSD&resolution=1&from=' +
    str(int(now)-60*500) + '&to=' + now)
    ohlcv = r.json()
    df_ = pd.DataFrame(ohlcv)
    df_ = df_.rename(columns = {"c":"close", "h":"high", "l":"low", "o":"open", "v":"value"})
    df_ = df_[["t", "close", "low",  "high", "open", "s", "value"]]

    time_date = []
    for i in df_.iloc[:,0]:
         time = datetime.datetime.fromtimestamp(i)
         time_date.append(time)
    dti = pd.DatetimeIndex(time_date)
    df_["t"] = dti
    df_ = df_.set_index("t")
    return df_

df = a(100, "300")
df = df.reset_index()
print(df)
