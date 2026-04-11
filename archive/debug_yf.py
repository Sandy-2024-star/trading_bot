import yfinance as yf
df = yf.download("BTC-USD", period="5d", interval="1h", progress=False)
print("Columns:", df.columns)
print("Index Name:", df.index.name)
print("Sample Head:\n", df.head())
