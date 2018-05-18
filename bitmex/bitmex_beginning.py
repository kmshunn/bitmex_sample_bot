from time import sleep
import ccxt
import requests

exchanges = {
    "bitmex": {
        "apiKey": "VHppd1wDBRP3gAcyFGnb1A6f",
        "secret": "ESffLhyr1SSum1mQ-fiRTlNaK8wtAujeP-MFXLaFYzXimch3"
    },
}

bitmex = ccxt.bitmex()
bitmex.apiKey = exchanges["bitmex"]["apiKey"]
bitmex.secret = exchanges["bitmex"]["secret"]

bitmex.urls['api'] = bitmex.urls['test']

amount = 10
sleep = 60

def orderbook():
    orderbook = bitmex.fetch_order_book ('BTC/USD')
    bid = orderbook['bids'][0][0] if len (orderbook['bids']) > 0 else None
    ask = orderbook['asks'][0][0] if len (orderbook['asks']) > 0 else None
    spread = (ask - bid) if (bid and ask) else None
    print (bitmex.id, 'market price', { 'bid': bid, 'ask': ask, 'spread': spread })


#成行
def market(side, size): # 成行発注用の関数
    a = "Order: Market. Side : {}  size : {}".format(side,size)
    print(a)
    bitmex.create_order(symbol='BTC/USD', type='market', side=side, amount=size)
    line_notify(a)

#指値
def limit(side, price, size):
    print("Order: Limit. Side : {}  size : {}".format(side,size))
    limit = bitmex.create_order('BTC/USD', type='limit', side=side, amount=size, price=price)
    message = ("Order: Limit. Side : {}".format(side))
    return limit
    return line_notify(message)

#positionの確認
def position():
    pos = bitmex.private_get_position()[1]
    if pos['currentQty'] == 0: # sizeが0より大きければ現在LONG状態、0より小さければ現在SHORT状態と判断
        side = 'NO POSITION'
    elif pos['currentQty'] > 0:
        side = 'LONG'
    else:
        side = 'SHORT'
    return {'side': side, 'size': round(pos['currentQty']), 'avgEntryPrice': pos['avgEntryPrice']}

def line_notify(message):
    line_notify_token = 'fVXGnTYKe6uORVNOJJzwbpqzUwTpPr01YZWkq3H1X7o'
    line_notify_api = 'https://notify-api.line.me/api/notify'



    payload = {'message': message}
    headers = {'Authorization': 'Bearer ' + line_notify_token}  # 発行したトークン
    line_message = requests.post(line_notify_api, data=payload, headers=headers)
    print(payload)
    line_message

print(ccxt.bitmex().fetch_ticker('BTC/USD'))
