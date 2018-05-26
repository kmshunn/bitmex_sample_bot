import ccxt

key = "VHppd1wDBRP3gAcyFGnb1A6f"
secret = "ESffLhyr1SSum1mQ-fiRTlNaK8wtAujeP-MFXLaFYzXimch3"

bitmex = ccxt.bitmex({
'apiKey' : key,
'secret' : secret
})
product_code = 'BTC/USD'

bitmex.urls['api'] = bitmex.urls['test']

ticker = bitmex.fetch_ticker(product_code)
print(ticker['bid'])
