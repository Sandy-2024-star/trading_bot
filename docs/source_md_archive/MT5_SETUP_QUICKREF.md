# MT5 Quick Setup Reference

## 5-Minute Setup

### 1. Get MetaApi Account (2 min)
```
1. Go to: https://app.metaapi.cloud
2. Click: Sign Up (FREE)
3. Verify email
```

### 2. Connect MT5 (2 min)
```
1. Open MT5 platform
2. Tools → Options → Community
3. Login with MetaQuotes ID
4. Enable: Allow algorithmic trading
5. Login to trading account
```

### 3. Get Credentials (1 min)
```
1. Dashboard → Create account
2. Select: MetaTrader broker server
3. Enter broker server address
4. Copy Account ID
5. Generate API token
```

### 4. Install (30 sec)
```bash
pip install metaapi-python-sdk
```

### 5. Configure (.env)
```bash
METAAPI_TOKEN="your-token"
METAAPI_ACCOUNT_ID="your-account-id"
```

---

## Test Connection
```python
from metaapi_cloud_sdk import MetaApi

api = MetaApi(token="YOUR_TOKEN")
account = await api.metatrader_account_api.get_account("ACCOUNT_ID")
print(f"Balance: {account.balance}")
```

---

## Free Tier Limits
| Metric | Limit |
|--------|-------|
| Transactions | 500/month |
| Historical candles | Unlimited |
| Accounts | 1 |

---

## Symbols Quick Reference
```
Forex:     EURUSD, GBPUSD, USDJPY, USDINR
Commodities: XAUUSD (Gold), XAGUSD (Silver)
Indices:    US100, US30, GER40, IND50
```

---

## Commands

| Action | Command |
|--------|---------|
| Connect | `await account.connect()` |
| Status | `account.connection_status` |
| Prices | `await account.get_symbol_price(symbol)` |
| Order | `await account.create_market_order(...)` |
| Close | `await account.close_position(id)` |
