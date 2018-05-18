import ccxt


bitmex = ccxt.bitmex({
    'apiKey': 'VHppd1wDBRP3gAcyFGnb1A6f',
    'secret': 'ESffLhyr1SSum1mQ-fiRTlNaK8wtAujeP-MFXLaFYzXimch3',
})

print(bitmex.fetch_ticker('BTC/USD'))
