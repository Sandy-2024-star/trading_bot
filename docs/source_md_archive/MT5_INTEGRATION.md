# MT5 Integration Guide

## Overview

MetaTrader 5 (MT5) integration enables your trading bot to trade **Forex, Commodities, Indices, and Stocks** through your MT5 account.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    METAAPI CLOUD ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Your Trading Bot        MetaApi Cloud         MT5 Server         │
│   ┌──────────────┐      ┌──────────┐       ┌───────────┐        │
│   │              │ ───► │          │ ────► │           │        │
│   │  Python SDK  │      │  REST/   │       │  MT5      │        │
│   │              │ ◄─── │  WebSocket│ ◄─── │  Terminal │        │
│   │              │      │          │       │           │        │
│   └──────────────┘      └──────────┘       └───────────┘        │
│         │                   │                   │                │
│         └───────────────────┴───────────────────┘               │
│                    No DLL Required                                │
└─────────────────────────────────────────────────────────────────┘
```

## Why MetaApi Cloud?

| Feature | Benefit |
|---------|---------|
| FREE tier | 500 transactions/month (no cost) |
| No DLL | Works without local MT5 DLL |
| Cloud-based | Run bot anywhere, any VPS |
| WebSocket | Real-time price streaming |
| MT4/MT5 | Supports both platforms |
| Python SDK | Official Python support |

## Supported Markets

| Market | Symbols | Example |
|--------|---------|---------|
| **Forex** | Major, Minor, Exotic | EUR/USD, GBP/JPY, USD/INR |
| **Commodities** | Metals, Energy | XAUUSD (Gold), XTIUSD (Oil) |
| **Indices** | Global Indices | US100, US30, GER40 |
| **Stocks** | Individual Shares | AAPL, TSLA, RELIANCE |
| **Crypto** | Broker dependent | BTCUSD |

---

## Setup Guide

### Prerequisites

1. MT5 Platform installed
2. MT5 Trading account
3. MetaApi Cloud account

### Step 1: Create MetaApi Account

1. Go to: https://app.metaapi.cloud
2. Sign up for FREE account
3. Note your **API Token**

### Step 2: Connect MT5 Terminal

1. Open **MetaTrader 5** platform
2. Go to: `Tools` → `Options` → `Community`
3. Login with your **MetaQuotes ID**
4. Enable: `Allow algorithmic trading`
5. Login to your trading account

### Step 3: Create MetaApi Application

1. Go to: https://app.metaapi.cloud
2. Click: `Create new account`
3. Select: `MetaTrader broker server`
4. Enter: Your broker's MT5 server address
5. Wait for account to sync (5-10 minutes)

### Step 4: Get Account ID

1. In MetaApi dashboard, click your account
2. Copy the **Account ID**
3. Example: `ab cd1234-5678-90ef-gh12-345678901234`

---

## Installation

### Install Python SDK

```bash
pip install metaapi-python-sdk
```

### Configuration

Add to `trading_bot/config/.env`:

```bash
# MetaApi Cloud (MT5)
METAAPI_TOKEN="your-metaapi-api-token"
METAAPI_ACCOUNT_ID="your-account-id"
```

---

## Usage Examples

### Basic Connection

```python
import asyncio
from metaapi_cloud_sdk import MetaApi

async def connect_to_mt5():
    api = MetaApi(token="YOUR_TOKEN")
    
    try:
        account = await api.metatrader_account_api.get_account("ACCOUNT_ID")
        
        # Wait for terminal to connect
        if account.connection_status != 'connected':
            await account.connect()
            await account.wait_connected()
        
        print(f"Connected to {account.name}")
        print(f"Balance: {account.balance}")
        print(f"Equity: {account.equity}")
        
    except Exception as e:
        print(f"Connection error: {e}")

asyncio.run(connect_to_mt5())
```

### Get Market Data

```python
from metaapi_cloud_sdk import MetaApi

async def get_market_data():
    api = MetaApi(token="YOUR_TOKEN")
    account = await api.metatrader_account_api.get_account("ACCOUNT_ID")
    
    # Get current prices
    symbol = "EURUSD"
    specification = await account.get_symbol_specification(symbol)
    price = await account.get_symbol_price(symbol)
    
    print(f"{symbol}:")
    print(f"  Bid: {price.bid}")
    print(f"  Ask: {price.ask}")
    print(f"  Spread: {price Spread}")
    
    # Get candles
    candles = await account.get_historical_candles(
        symbol=symbol,
        timeframe="H1",
        from_time=datetime.now() - timedelta(days=7),
        to_time=datetime.now()
    )
    print(f"Candles: {len(candles)}")
    
    return price, candles
```

### Place Order

```python
async def place_order():
    api = MetaApi(token="YOUR_TOKEN")
    account = await api.metatrader_account_api.get_account("ACCOUNT_ID")
    
    # Place market order
    order = await account.create_market_order(
        symbol="EURUSD",
        side="buy",  # or "sell"
        volume=0.1,  # Lot size
        stop_loss=1.0800,   # Optional SL
        take_profit=1.0950  # Optional TP
    )
    
    print(f"Order placed: {order.id}")
    print(f"Status: {order.status}")
    print(f"Fill price: {order.fill_price}")
    
    return order
```

### Close Position

```python
async def close_position():
    api = MetaApi(token="YOUR_TOKEN")
    account = await api.metatrader_account_api.get_account("ACCOUNT_ID")
    
    # Get positions
    positions = await account.get_positions()
    
    for position in positions:
        print(f"Position: {position.id}")
        print(f"  Symbol: {position.symbol}")
        print(f"  Side: {position.side}")
        print(f"  Volume: {position.volume}")
        print(f"  PnL: {position.profit}")
        
        # Close specific position
        if position.symbol == "EURUSD":
            await account.close_position(position.id)
            print(f"Closed position: {position.id}")
```

### Get Historical Data

```python
from datetime import datetime, timedelta

async def get_historical():
    api = MetaApi(token="YOUR_TOKEN")
    account = await api.metatrader_account_api.get_account("ACCOUNT_ID")
    
    # Get last 100 candles
    candles = await account.get_historical_candles(
        symbol="XAUUSD",
        timeframe="H1",
        limit=100
    )
    
    # Convert to pandas DataFrame
    import pandas as pd
    
    df = pd.DataFrame([{
        'time': c.time,
        'open': c.open,
        'high': c.high,
        'low': c.low,
        'close': c.close,
        'volume': c.volume
    } for c in candles])
    
    return df
```

---

## API Reference

### MetaApi Class

```python
from metaapi_cloud_sdk import MetaApi

api = MetaApi(token="YOUR_TOKEN")

# Access APIs
account_api = api.metatrader_account_api
```

### Account Methods

| Method | Description |
|--------|-------------|
| `connect()` | Connect to MT5 terminal |
| `disconnect()` | Disconnect from terminal |
| `wait_connected()` | Wait for connection |
| `get_positions()` | Get all open positions |
| `get_orders()` | Get pending orders |
| `get_symbol_price(symbol)` | Get current price |
| `get_symbol_specification(symbol)` | Get symbol details |
| `get_historical_candles()` | Get OHLCV data |
| `create_market_order()` | Place market order |
| `create_limit_order()` | Place limit order |
| `create_stop_order()` | Place stop order |
| `close_position(id)` | Close position |
| `cancel_order(id)` | Cancel pending order |

### Order Types

```python
# Market Order - Immediate execution
await account.create_market_order(
    symbol="EURUSD",
    side="buy",
    volume=0.1
)

# Limit Order - Place at specific price
await account.create_limit_order(
    symbol="EURUSD",
    side="buy",
    volume=0.1,
    open_price=1.0800
)

# Stop Order - Trigger on price
await account.create_stop_order(
    symbol="EURUSD",
    side="buy",
    volume=0.1,
    open_price=1.0850
)
```

### Order Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `symbol` | str | Trading symbol |
| `side` | str | "buy" or "sell" |
| `volume` | float | Lot size |
| `open_price` | float | Limit/Stop price |
| `stop_loss` | float | SL price |
| `take_profit` | float | TP price |
| `comment` | str | Order comment |

---

## MT5 Symbols Reference

### Forex (Major)

| Symbol | Description |
|--------|-------------|
| EURUSD | Euro / US Dollar |
| GBPUSD | British Pound / US Dollar |
| USDJPY | US Dollar / Japanese Yen |
| USDCHF | US Dollar / Swiss Franc |
| AUDUSD | Australian Dollar / US Dollar |
| USDCAD | US Dollar / Canadian Dollar |
| NZDUSD | New Zealand Dollar / US Dollar |

### Forex (Crosses)

| Symbol | Description |
|--------|-------------|
| EURGBP | Euro / British Pound |
| EURJPY | Euro / Japanese Yen |
| GBPJPY | British Pound / Japanese Yen |
| AUDJPY | Australian Dollar / Japanese Yen |
| EURCHF | Euro / Swiss Franc |
| EURCAD | Euro / Canadian Dollar |
| USDINR | US Dollar / Indian Rupee |

### Commodities

| Symbol | Description |
|--------|-------------|
| XAUUSD | Gold / US Dollar |
| XAGUSD | Silver / US Dollar |
| XTIUSD | Crude Oil (WTI) |
| XBRUSD | Crude Oil (Brent) |

### Indices

| Symbol | Description |
|--------|-------------|
| US100 | US Tech 100 |
| US30 | Dow Jones 30 |
| US500 | S&P 500 |
| GER40 | DAX 40 |
| UK100 | FTSE 100 |
| JPN225 | Nikkei 225 |
| IND50 | Nifty 50 |

---

## Rate Limits & Costs

### MetaApi Pricing

| Plan | Transactions | Cost |
|------|--------------|------|
| **FREE** | 500/month | $0 |
| Starter | 10,000/month | $15/month |
| Professional | 100,000/month | $75/month |
| Enterprise | Unlimited | Custom |

### Transaction Types

Each API call counts as 1 transaction:
- Price check
- Order placement
- Position close
- Historical data (per candle)

### Tips to Minimize Usage

```python
# Cache prices (don't call every tick)
cache = {}
cache_time = 0

async def get_cached_price(symbol):
    global cache_time
    if time.time() - cache_time > 1:  # Cache 1 second
        cache['price'] = await account.get_symbol_price(symbol)
        cache_time = time.time()
    return cache['price']
```

---

## Error Handling

```python
async def safe_order():
    try:
        order = await account.create_market_order(
            symbol="EURUSD",
            side="buy",
            volume=0.1
        )
        return order
    except OrderRejectedException as e:
        print(f"Order rejected: {e}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Connection timeout` | No internet/MT5 offline | Check connection |
| `Invalid symbol` | Wrong symbol format | Use correct symbol |
| `Insufficient margin` | Not enough balance | Reduce volume |
| `Market closed` | Trading halted | Check broker hours |
| `Invalid volume` | Wrong lot size | Check min/max lot |

---

## Best Practices

### 1. Always Use Stop Loss

```python
await account.create_market_order(
    symbol="EURUSD",
    side="buy",
    volume=0.1,
    stop_loss=1.0800,    # ALWAYS set SL
    take_profit=1.0950   # TP recommended
)
```

### 2. Handle Reconnections

```python
# Listen for disconnection
account.add_synchronization_listener(your_listener)

async def on_disconnected():
    print("Disconnected, reconnecting...")
    await account.connect()
    await account.wait_connected()
```

### 3. Batch Requests

```python
# Instead of:
for symbol in symbols:
    price = await account.get_symbol_price(symbol)

# Do:
prices = await asyncio.gather(*[
    account.get_symbol_price(s) for s in symbols
])
```

### 4. Use Correct Timeframes

```python
timeframes = {
    "M1": "1m",
    "M5": "5m",
    "M15": "15m",
    "H1": "1h",
    "H4": "4h",
    "D1": "1d"
}
```

---

## Troubleshooting

### Connection Issues

```bash
# Check MT5 is running
# Check internet connection
# Verify MetaQuotes ID logged in
# Check broker server address
```

### Order Not Executing

```bash
# Check market is open
# Verify sufficient margin
# Check stop levels are valid
# Check lot size within limits
```

### Getting Historical Data

```bash
# Check date range is valid
# Ensure timeframe is supported
# Verify symbol exists
```

---

## Security Notes

- **Never share** your API token
- **Store** tokens in environment variables
- **Use** paper trading first
- **Test** with small volumes
- **Monitor** positions regularly

---

## Resources

- MetaApi Dashboard: https://app.metaapi.cloud
- Documentation: https://metaapi.cloud/docs/
- Python SDK: https://github.com/metaapi/metaapi-python-sdk
- MT5 Download: https://www.metatrader5.com

---

## Next Steps

1. Get MetaApi account: https://app.metaapi.cloud
2. Connect your MT5 terminal
3. Get API credentials
4. Configure trading bot
5. Test with paper trading
6. Go live with small amounts

---

## Integration with Trading Bot

### Existing Files to Reuse

| File | Purpose | How to Use |
|------|---------|------------|
| `data/base_feed.py` | Market data interface | `MT5Feed(MarketDataFeed)` |
| `execution/base_broker.py` | Broker interface | `MT5Broker(BaseBroker)` |
| `execution/paper_broker.py` | Reference implementation | Copy pattern for MT5Broker |
| `execution/order_manager.py` | Order coordination | Already works with any broker |
| `data/factory.py` | Provider selection | Add MT5 case |
| `data/market_registry.py` | Symbol routing | Add MT5 routing |

### Files to Create

| File | Lines | Purpose |
|------|-------|---------|
| `data/mt5_feed.py` | ~150 | MT5 market data |
| `execution/mt5_broker.py` | ~250 | MT5 execution |

### Files to Update

| File | Changes |
|------|---------|
| `config/config.py` | +2 lines (METAAPI_* settings) |
| `data/factory.py` | +5 lines (MT5 case) |
| `data/market_registry.py` | +5 lines (MT5 routing) |
| `requirements.txt` | +1 line (metaapi-python-sdk) |
| `main.py` | +30 lines (demo_mt5 phase) |

### Complete Implementation Guide

See `MT5_IMPLEMENTATION_PLAN.md` for step-by-step implementation.

### Quick Test After Setup

```bash
# Test connection
python -c "
import asyncio
from metaapi_cloud_sdk import MetaApi
api = MetaApi(token='YOUR_TOKEN')
account = await api.metatrader_account_api.get_account('YOUR_ACCOUNT_ID')
print(f'Balance: {account.balance}')
"
```

---

## Project-Specific Notes

### Why This Architecture Works

1. **BaseBroker abstraction**: MT5Broker just implements the same interface as PaperBroker
2. **OrderManager already generic**: Works with any broker
3. **Factory pattern**: Easy to add new providers
4. **Registry pattern**: Automatic symbol routing

### Symbol Mapping

| Bot Symbol | MT5 Symbol | Market |
|-----------|------------|--------|
| EURUSD | EURUSD | Forex |
| GBPUSD | GBPUSD | Forex |
| XAUUSD | XAUUSD | Commodity |
| US100 | US100 | Index |

### Order Type Mapping

| Bot OrderType | MT5 Equivalent |
|---------------|-----------------|
| MARKET | Market order |
| LIMIT | Limit order |
| STOP_LOSS | Stop order |
| TAKE_PROFIT | Take profit order |

---

## Full Implementation Order

1. **Setup MetaApi** → Create account, connect MT5
2. **Install SDK** → `pip install metaapi-python-sdk`
3. **Update Config** → Add METAAPI_* to config.py and .env
4. **Create MT5Feed** → `data/mt5_feed.py`
5. **Create MT5Broker** → `execution/mt5_broker.py`
6. **Update Factory** → Add MT5 to provider selection
7. **Update Registry** → Add MT5 symbol routing
8. **Update Main** → Add demo_mt5 phase
9. **Test** → Run `python main.py mt5`
