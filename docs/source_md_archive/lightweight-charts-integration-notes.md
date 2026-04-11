# Lightweight Charts Integration Notes

## Goal

Prepare a clean payload boundary between the Python backend and the future
Lightweight Charts frontend rendering layer.

## Backend Responsibilities

The Python side should:

- fetch candles from the configured market-data feed
- normalize them into one stable JSON structure
- attach optional overlay data for entry, exit, stop-loss, and take-profit
- emit structured strategy decisions that execution and visualization can share
- avoid embedding chart-library-specific logic in strategy code too early

## Frontend Responsibilities

The chart-rendering side should:

- render candlesticks from normalized candle data
- apply markers for entries and exits
- apply price lines for stop-loss and take-profit
- keep visual styling separate from trade decision logic
- never become the primary decision-maker for trade logic

## Proposed Payload Split

Suggested JSON response shape:

```json
{
  "symbol": "BTCUSD",
  "timeframe": "1h",
  "candles": [
    {
      "time": 1711929600,
      "open": 69500.12,
      "high": 70125.4,
      "low": 68950.1,
      "close": 69980.55
    }
  ],
  "decision": {
    "status": "enter_long",
    "reason_codes": ["signal_threshold_passed", "candle_close_confirmed"],
    "entry_price": 69980.55,
    "stop_loss": 67881.13,
    "take_profit": 73479.58
  },
  "overlays": {
    "markers": [],
    "price_lines": []
  }
}
```

## First Integration Boundary

For the first pass, use R&D outputs only:

- generate candle payloads in `RND/scripts/chart_snapshot.py`
- keep sample overlays synthetic until entry and exit rules are finalized
- define a structured decision payload before wiring real chart annotations
- promote the payload contract into the dashboard only after it is stable

## Known Constraint

Current CoinGecko candle data includes a `volume` column in the dataframe, but
it is not coming from a full exchange volume stream in the current adapter.

That means:

- candlestick rendering is fine for R&D
- volume-based trading logic should not be trusted yet
- volume overlays should stay out of scope for the first chart milestone
