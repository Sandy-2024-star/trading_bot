# Lightweight Charts Selection

## Decision

Selected chart library for the current R&D track:

- `TradingView Lightweight Charts`

## Why It Fits This Repo

The current application already serves HTML through the FastAPI dashboard in
`monitoring/web_dashboard.py`.

That makes this chart choice practical because we can:

- keep the backend in Python
- add chart rendering in the existing web dashboard path
- feed candlestick data from current market-data modules
- overlay entry, exit, stop-loss, and take-profit visuals without changing the
  rest of the trading engine first

## Initial Scope

Use the library for:

- candlestick chart rendering
- chart time scale and price scale interaction
- entry markers
- exit markers
- stop-loss lines
- take-profit lines

Important role boundary:

- the chart is for visualization and operator inspection
- the strategy system remains the source of truth for trade decisions
- chart overlays should display what the strategy decided, not drive the
  decision process

Do not expand scope yet into:

- full drawing-tool systems
- broker-side chart trading
- multi-layout workstation features
- indicator overload in the first pass

## Practical Integration Direction

Likely path:

1. Prepare candles in Python from the existing feed.
2. Expose chart-ready JSON from the dashboard backend.
3. Render the chart in the dashboard HTML and JavaScript layer.
4. Add entry and exit markers.
5. Add stop-loss and take-profit horizontal lines.
6. Connect those overlays to structured strategy decisions.
7. Validate the end-to-end chart-to-trade flow in `RND` before promotion.

## Next Deliverables

- `RND/docs/chart-data-requirements.md`
- `RND/docs/lightweight-charts-integration-notes.md`
- `RND/scripts/chart_snapshot.py`

## Promotion Trigger

After the R&D flow proves stable, move the validated implementation into:

- `monitoring/web_dashboard.py`
- dashboard data endpoints
- related strategy and risk modules where required
