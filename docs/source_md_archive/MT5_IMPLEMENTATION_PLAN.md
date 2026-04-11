# MT5 Implementation Plan

## Quick Reference

### Files to Create
| File | Purpose | Lines |
|------|---------|-------|
| `data/mt5_feed.py` | MT5 market data feed | ~150 |
| `execution/mt5_broker.py` | MT5 broker adapter | ~250 |

### Files to Update
| File | Changes |
|------|---------|
| `config/config.py` | Add METAAPI_TOKEN, METAAPI_ACCOUNT_ID |
| `data/factory.py` | Add MT5 to provider selection |
| `data/market_registry.py` | Add MT5 symbol routing |
| `requirements.txt` | Add metaapi-python-sdk |
| `main.py` | Add demo_mt5 phase |

### Files to Reuse
- `data/base_feed.py` - Inherit MarketDataFeed
- `execution/base_broker.py` - Inherit BaseBroker
- `execution/paper_broker.py` - Reference implementation
- `execution/order_manager.py` - Works with MT5Broker (no changes)

---

## Step-by-Step Implementation

### Step 1: Setup MetaApi (Do First)

```bash
# 1. Create account: https://app.metaapi.cloud
# 2. Connect MT5: Tools → Options → Community → Login
# 3. Get API token from dashboard
# 4. Install SDK
pip install metaapi-python-sdk
```

### Step 2: Add Config Settings

Edit `config/config.py`:

```python
# Add after existing broker settings (~line 55)
# MetaApi (MT5)
METAAPI_TOKEN = os.getenv("METAAPI_TOKEN", "")
METAAPI_ACCOUNT_ID = os.getenv("METAAPI_ACCOUNT_ID", "")
```

Edit `config/.env`:

```bash
# MetaApi (MT5)
METAAPI_TOKEN="your-token-here"
METAAPI_ACCOUNT_ID="your-account-id-here"
```

### Step 3: Update Requirements

Edit `requirements.txt`:

```txt
# Add at end
metaapi-python-sdk>=5.0.0
```

### Step 4: Create MT5 Data Feed

Create `data/mt5_feed.py`:

```python
"""
MT5 market data feed using MetaApi cloud.
"""

import asyncio
from typing import Dict, List, Optional
import pandas as pd
from loguru import logger

from data.base_feed import MarketDataFeed

class MT5Feed(MarketDataFeed):
    """MT5 data feed via MetaApi cloud."""
    
    def __init__(self, api_token: str, account_id: str):
        self.api_token = api_token
        self.account_id = account_id
        self._api = None
        self._account = None
        
    async def connect(self):
        from metaapi_cloud_sdk import MetaApi
        self._api = MetaApi(token=self.api_token)
        self._account = await self._api.metatrader_account_api.get_account(self.account_id)
        await self._account.connect()
        await self._account.wait_connected()
        logger.info(f"MT5Feed connected to account {self.account_id}")
    
    async def close(self):
        if self._account:
            await self._account.disconnect()
    
    async def get_ticker(self, symbol: str) -> Optional[Dict]:
        # Implementation...
    
    async def get_candlesticks(self, symbol: str, timeframe: str = "1h", limit: int = 100) -> pd.DataFrame:
        # Implementation...
    
    async def get_orderbook(self, symbol: str, depth: int = 10) -> Optional[Dict]:
        # Implementation...
```

### Step 5: Create MT5 Broker

Create `execution/mt5_broker.py`:

```python
"""
MT5 broker implementation using MetaApi cloud.
"""

import asyncio
from typing import Dict, List, Optional
from loguru import logger

from execution.base_broker import (
    BaseBroker, Order, OrderStatus, OrderSide, OrderType
)

class MT5Broker(BaseBroker):
    """MT5 broker via MetaApi cloud."""
    
    def __init__(self, api_token: str, account_id: str):
        super().__init__("MT5Broker")
        self.api_token = api_token
        self.account_id = account_id
        self._api = None
        self._account = None
        
    async def connect(self):
        from metaapi_cloud_sdk import MetaApi
        self._api = MetaApi(token=self.api_token)
        self._account = await self._api.metatrader_account_api.get_account(self.account_id)
        await self._account.connect()
        await self._account.wait_connected()
        logger.info(f"MT5Broker connected to {self.account_id}")
    
    async def disconnect(self):
        if self._account:
            await self._account.disconnect()
    
    async def place_order(self, symbol, side, order_type, quantity, price=None, stop_price=None) -> Order:
        # Market order
        if order_type == OrderType.MARKET:
            order = await self._account.create_market_order(
                symbol=symbol,
                side=side.value,
                volume=quantity
            )
        # Limit order
        elif order_type == OrderType.LIMIT:
            order = await self._account.create_limit_order(
                symbol=symbol,
                side=side.value,
                volume=quantity,
                open_price=price
            )
        # ... other order types
        return order
    
    async def cancel_order(self, order_id: str) -> bool:
        await self._account.cancel_order(order_id)
        return True
    
    async def get_order(self, order_id: str) -> Optional[Order]:
        # Implementation...
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        # Implementation...
    
    async def get_account_balance(self) -> float:
        account_info = await self._account.get_account_information()
        return account_info.balance
    
    async def get_position(self, symbol: str) -> float:
        # Implementation...
    
    async def get_current_price(self, symbol: str) -> float:
        price = await self._account.get_symbol_price(symbol)
        return price.bid
```

### Step 6: Update Factory

Edit `data/factory.py`:

```python
def create_market_data_feed(provider: str = None):
    selected_provider = (provider or config.MARKET_DATA_PROVIDER).lower()
    
    if selected_provider == "crypto_com":
        return CryptoFeed()
    if selected_provider == "coingecko":
        return CoinGeckoFeed()
    if selected_provider == "mt5":
        from data.mt5_feed import MT5Feed
        return MT5Feed(config.METAAPI_TOKEN, config.METAAPI_ACCOUNT_ID)
    
    raise ValueError(f"Unsupported provider: {selected_provider}")
```

### Step 7: Update Market Registry

Edit `data/market_registry.py`:

```python
# In __init__:
self.feeds["mt5"] = MT5Feed(config.METAAPI_TOKEN, config.METAAPI_ACCOUNT_ID)

# In get_feed_for_symbol:
# Add after forex check:
if any(curr in upper_symbol for curr in ["XAU", "XAG", "US", "DE", "UK", "JPN"]):
    return self.feeds.get("mt5")
```

### Step 8: Add MT5 Phase to Main

Edit `main.py`:

```python
# Add import
from execution.mt5_broker import MT5Broker

# Add function
async def demo_mt5():
    """Demo Phase 5: MT5 Live Trading"""
    logger.info("=== MT5 Live Trading Demo ===")
    
    broker = MT5Broker(config.METAAPI_TOKEN, config.METAAPI_ACCOUNT_ID)
    await broker.connect()
    
    try:
        # Get account info
        balance = await broker.get_account_balance()
        logger.info(f"Account Balance: ${balance:,.2f}")
        
        # Get price
        price = await broker.get_current_price("EURUSD")
        logger.info(f"EURUSD: {price}")
        
        # Place order (demo)
        order = await broker.place_order(
            symbol="EURUSD",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=0.1
        )
        logger.info(f"Order placed: {order}")
        
    finally:
        await broker.disconnect()

# Update main() to handle mt5
def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "mt5":
            asyncio.run(demo_mt5())
        # ... other phases
```

---

## Running MT5 Mode

```bash
# Set environment
export METAAPI_TOKEN="your-token"
export METAAPI_ACCOUNT_ID="your-account-id"

# Run MT5 demo
cd trading_bot
python main.py mt5
```

---

## Testing Checklist

- [ ] MetaApi account created
- [ ] MT5 terminal connected
- [ ] API credentials obtained
- [ ] SDK installed (`pip install metaapi-python-sdk`)
- [ ] Config updated (METAAPI_TOKEN, METAAPI_ACCOUNT_ID)
- [ ] MT5Feed created
- [ ] MT5Broker created
- [ ] Factory updated
- [ ] Registry updated
- [ ] Main updated
- [ ] Connection test passed
- [ ] Order placement test passed
- [ ] Position check test passed
