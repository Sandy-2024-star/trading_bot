# MT5 Integration - Project Analysis & Implementation Plan

## Current Project Structure Analysis

### Existing Files That Can Be Reused

```
trading_bot/
├── data/
│   ├── base_feed.py           ✅ REUSE - Inherit MarketDataFeed interface
│   ├── factory.py             ✅ REUSE - Add MT5 to provider selection
│   ├── market_registry.py     ✅ REUSE - Add MT5 symbol routing
│   ├── yfinance_feed.py       ✅ REUSE - Can provide data for MT5 strategies
│   ├── ccxt_feed.py          ✅ REUSE - Can provide data for MT5 strategies
│   └── crypto_feed.py         ✅ REUSE - Existing pattern to follow
│
├── execution/
│   ├── base_broker.py         ✅ REUSE - Inherit BaseBroker for MT5Broker
│   ├── paper_broker.py        ✅ REUSE - Reference implementation
│   ├── order_manager.py       ✅ REUSE - Already coordinates broker + strategy
│   └── backtester.py          ✅ REUSE - Already uses broker interface
│
├── config/
│   └── config.py              🔄 UPDATE - Add METAAPI_* settings
│
├── main.py                    🔄 UPDATE - Add MT5 execution mode
│
└── requirements.txt           🔄 UPDATE - Add metaapi-python-sdk
```

### New Files To Create

```
trading_bot/
├── data/
│   └── mt5_feed.py            🆕 NEW - MT5 market data feed
│
├── execution/
│   └── mt5_broker.py          🆕 NEW - MT5 broker implementation
│
└── scripts/
    └── mt5_test_connection.py 🆕 NEW - Connection test script
```

---

## Existing Architecture - MT5 Integration Points

### 1. Data Layer (`data/`)

#### base_feed.py - Existing Interface
```python
class MarketDataFeed(ABC):
    @abstractmethod
    async def connect(self): pass
    @abstractmethod
    async def close(self): pass
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Optional[Dict]: pass
    @abstractmethod
    async def get_candlesticks(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame: pass
    @abstractmethod
    async def get_orderbook(self, symbol: str, depth: int) -> Optional[Dict]: pass
```

**MT5 Action**: Create `mt5_feed.py` that inherits `MarketDataFeed`

#### factory.py - Provider Selection
```python
def create_market_data_feed(provider: str = None):
    if provider == "crypto_com": return CryptoFeed()
    if provider == "coingecko": return CoinGeckoFeed()
    # Add: if provider == "mt5": return MT5Feed()
```

**MT5 Action**: Add MT5 to factory

#### market_registry.py - Symbol Routing
```python
def get_feed_for_symbol(self, symbol: str):
    # Forex symbols -> MT5
    # Gold/Oil -> MT5
    # Indices -> MT5
```

**MT5 Action**: Add MT5 feed for Forex/Commodities/Indices

---

### 2. Execution Layer (`execution/`)

#### base_broker.py - Broker Interface
```python
class BaseBroker(ABC):
    @abstractmethod
    async def connect(self): pass
    @abstractmethod
    async def disconnect(self): pass
    @abstractmethod
    async def place_order(self, symbol, side, order_type, quantity, price, stop_price): pass
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool: pass
    @abstractmethod
    async def get_order(self, order_id: str): pass
    @abstractmethod
    async def get_open_orders(self, symbol: Optional[str] = None): pass
    @abstractmethod
    async def get_account_balance(self) -> float: pass
    @abstractmethod
    async def get_position(self, symbol: str) -> float: pass
    @abstractmethod
    async def get_current_price(self, symbol: str) -> float: pass
```

**MT5 Action**: Create `mt5_broker.py` that inherits `BaseBroker`

#### paper_broker.py - Reference Implementation
- Shows complete broker implementation
- Has fee calculation, slippage simulation
- Order lifecycle management

**MT5 Action**: Reference for MT5Broker implementation

#### order_manager.py - Already Works With Any Broker
```python
class OrderManager:
    def __init__(self, broker: BaseBroker, ...):  # Takes any broker!
```

**MT5 Action**: No changes needed - plug in MT5Broker

---

### 3. Config Layer (`config/`)

#### config.py - Current Settings
```python
# Existing broker settings
CRYPTO_COM_API_KEY = ...
OANDA_API_KEY = ...
REAL_BROKER_PROVIDER = "oanda"  # Can change to "mt5"
EXECUTION_MODE = "paper"  # Can change to "live"
```

**MT5 Action**: Add METAAPI_* settings

---

### 4. Main Entry Point (`main.py`)

#### Current Phase Structure
```python
async def demo_phase1():  # Data + signals
async def demo_phase2():  # Strategy + risk
async def demo_phase3():  # Backtesting
async def demo_phase4():  # Live trading
async def demo_web():     # Web dashboard
```

**MT5 Action**: Add `demo_mt5()` phase for MT5 live trading

---

## Implementation Roadmap

### Phase 1: Setup (No Code Changes)

```
Task 1.1: Create MetaApi Account
└── https://app.metaapi.cloud

Task 1.2: Connect MT5 Terminal
└── Tools → Options → Community → Login
└── Enable "Allow algorithmic trading"

Task 1.3: Get Credentials
├── Account ID
└── API Token

Task 1.4: Install SDK
└── pip install metaapi-python-sdk
```

### Phase 2: Create MT5 Data Feed (1 file)

```
File: trading_bot/data/mt5_feed.py
└── Inherits MarketDataFeed
└── Uses MetaApi SDK for market data
```

**Class Structure:**
```python
class MT5Feed(MarketDataFeed):
    def __init__(self, api_token: str, account_id: str):
        # Initialize MetaApi connection
    
    async def connect(self):
        # Connect to MetaApi
        # Login to MT5 account
    
    async def close(self):
        # Disconnect
    
    async def get_ticker(self, symbol: str):
        # Get current price
    
    async def get_candlesticks(self, symbol, timeframe, limit):
        # Get OHLCV data
    
    async def get_orderbook(self, symbol, depth):
        # Get market depth
```

### Phase 3: Create MT5 Broker (1 file)

```
File: trading_bot/execution/mt5_broker.py
└── Inherits BaseBroker
└── Uses MetaApi SDK for execution
```

**Class Structure:**
```python
class MT5Broker(BaseBroker):
    def __init__(self, api_token: str, account_id: str):
        # Initialize MetaApi connection
    
    async def connect(self):
        # Connect to MetaApi
    
    async def disconnect(self):
        # Disconnect
    
    async def place_order(self, symbol, side, order_type, quantity, price, stop_price):
        # Place order via MT5
    
    async def cancel_order(self, order_id):
        # Cancel pending order
    
    async def get_order(self, order_id):
        # Get order details
    
    async def get_open_orders(self, symbol=None):
        # Get open orders
    
    async def get_account_balance(self):
        # Get account balance
    
    async def get_position(self, symbol):
        # Get position size
    
    async def get_current_price(self, symbol):
        # Get current price
```

### Phase 4: Update Factory & Registry (Minimal Changes)

#### factory.py - Add MT5 Provider
```python
if selected_provider == "mt5":
    logger.info("Using MT5 as market data provider")
    from data.mt5_feed import MT5Feed
    return MT5Feed()
```

#### market_registry.py - Add MT5 Routing
```python
# MT5 covers: Forex, Commodities, Indices
mt5_symbols = ["EUR", "GBP", "JPY", "XAU", "XAG", "US", "DE", "UK"]
if any(s in upper_symbol for s in mt5_symbols):
    return self.feeds.get("mt5")
```

### Phase 5: Update Config (Add Settings)

```python
# config.py additions
METAAPI_TOKEN = os.getenv("METAAPI_TOKEN", "")
METAAPI_ACCOUNT_ID = os.getenv("METAAPI_ACCOUNT_ID", "")
```

### Phase 6: Add MT5 Demo Phase (main.py)

```python
async def demo_mt5():
    """Demo Phase 5: MT5 Live Trading"""
    # Initialize MT5 broker
    broker = MT5Broker(config.METAAPI_TOKEN, config.METAAPI_ACCOUNT_ID)
    await broker.connect()
    
    # Use existing strategy/risk logic
    strategy = TechnicalSignalStrategy(...)
    
    # Place orders via MT5
    order = await broker.place_order(...)
```

---

## File Change Summary

| File | Action | Lines Changed |
|------|--------|---------------|
| `requirements.txt` | UPDATE | +1 (metaapi-python-sdk) |
| `config/config.py` | UPDATE | +2 (METAAPI_* settings) |
| `data/mt5_feed.py` | CREATE | ~150 lines |
| `data/factory.py` | UPDATE | +5 lines (MT5 case) |
| `data/market_registry.py` | UPDATE | +5 lines (MT5 routing) |
| `execution/mt5_broker.py` | CREATE | ~250 lines |
| `main.py` | UPDATE | +30 lines (demo_mt5 phase) |
| **Total New Code** | | **~435 lines** |

---

## Integration Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         TRADING BOT                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐         ┌──────────────┐                    │
│   │   Strategy   │────────►│Order Manager │                    │
│   │              │         │              │                    │
│   └──────────────┘         └──────┬───────┘                    │
│                                  │                              │
│   ┌──────────────┐         ┌────▼───────┐                    │
│   │ Risk Manager │────────►│    Broker   │                    │
│   │              │         │             │                     │
│   └──────────────┘         └──────┬──────┘                    │
│                                  │                              │
│   ┌──────────────┐         ┌────▼──────────┐                   │
│   │ Data Feeds   │────────►│   MT5 Broker  │                   │
│   │  (yfinance,  │         │ (MetaApi SDK) │                   │
│   │   ccxt, MT5) │         └──────┬───────┘                    │
│   └──────────────┘                │                            │
│                                  │                            │
└──────────────────────────────────┼──────────────────────────────┘
                                   │
                    ┌───────────────┴───────────────┐
                    │         MetaApi Cloud           │
                    │      (metaapi.cloud)            │
                    └───────────────┬───────────────┘
                                   │
                    ┌───────────────┴───────────────┐
                    │        MT5 Terminal           │
                    │     (MT5 Platform)            │
                    └───────────────┬───────────────┘
                                   │
                    ┌───────────────┴───────────────┐
                    │       MT5 Broker Server        │
                    │  (Your Trading Account)        │
                    └───────────────────────────────┘
```

---

## Minimal Changes Approach

### Option A: Full Integration (Recommended)
- Add MT5Feed, MT5Broker
- Update factory/registry
- Full MT5 trading capability

### Option B: Minimal - Just Broker
- Only create MT5Broker
- Use existing yfinance_feed for data
- One MT5 broker, no MT5 data feed
- Faster to implement

### Option C: Separate Script
- Keep everything existing
- Create standalone `mt5_live_trading.py`
- Doesn't modify any existing files
- Run independently: `python mt5_live_trading.py`

---

## Recommended: Option A (Full Integration)

This gives you:
- MT5 for all execution (Forex, Gold, Indices)
- MT5 as a data source option
- Clean integration with existing strategy/risk logic
- Consistent with project architecture
