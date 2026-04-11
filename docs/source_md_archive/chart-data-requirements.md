# Chart Data Requirements

## Purpose

Define the minimum chart-data contract required for the current R&D track using
TradingView Lightweight Charts.

## Primary R&D Target

Initial chart target:

- provider: configured default market data provider
- expected default provider today: `coingecko`
- initial symbol: `BTCUSD`
- initial timeframe: `1h`

This can expand later, but the first workflow should validate one symbol and
one timeframe cleanly before broadening scope.

## Required Candle Fields

The chart and trade-logic experiments require these fields for every candle:

- `timestamp`
- `open`
- `high`
- `low`
- `close`
- `volume`

Current baseline:

- `CoinGeckoFeed.get_candlesticks()` already returns these columns
- `volume` is currently present but may be placeholder data depending on the
  provider response

## Lightweight Charts Candlestick Shape

Candlestick payload target:

```json
{
  "time": 1711929600,
  "open": 69500.12,
  "high": 70125.40,
  "low": 68950.10,
  "close": 69980.55
}
```

Notes:

- `time` should be a Unix timestamp in seconds
- OHLC values should be numeric
- candles must be sorted ascending by time

## Overlay Data Needed for Trade Visualization

### Entry and Exit Markers

Marker payload target:

```json
{
  "time": 1711929600,
  "position": "belowBar",
  "color": "#26a69a",
  "shape": "arrowUp",
  "text": "Entry 69980.55"
}
```

Required marker fields:

- `time`
- `position`
- `color`
- `shape`
- `text`

### Stop-Loss and Take-Profit Lines

Price line payload target:

```json
{
  "title": "SL",
  "price": 67881.13,
  "color": "#d32f2f",
  "lineStyle": "dashed"
}
```

Required price-line fields:

- `title`
- `price`
- `color`
- `lineStyle`

## Minimum History Requirements

For the first R&D cycle:

- preferred working range: `100` candles
- minimum practical history for indicator review: `50` candles
- preferred review sample in console output: last `5` candles

This leaves enough room for the existing technical indicators and for visual
checking of entry and exit placement.

## Validation Checklist

Before moving to entry-rule work, confirm:

- candles arrive in chronological order
- no required field is missing
- timestamps convert cleanly into chart time
- chart payload can be serialized as JSON
- entry, exit, stop-loss, and take-profit overlays can be attached to candle
  time and price values

## R&D Script

Reference script:

- `RND/scripts/chart_snapshot.py`
