import yfinance as yf

print('yfinance version:', yf.__version__)

ticker = yf.Ticker('AAPL')
data = ticker.history(period='5d')

print('AAPL data shape:', data.shape)

if not data.empty:
    print('Last close:', data['Close'].iloc[-1])
    print('SUCCESS!')
else:
    print('ERROR: No data returned')