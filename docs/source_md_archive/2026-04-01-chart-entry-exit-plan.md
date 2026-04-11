# Chart Access, Entry, Exit, Profit and Stop-Loss Plan

## Objective

Build the next trading workflow in stages inside `RND/`, starting from chart
data access and ending with a validated entry/exit flow that can later be
promoted into `main.py` and the production modules.

This track will focus on:

- chart access
- entry logic
- exit logic
- take-profit handling
- stop-loss handling

## Operating Model

This track must support an autonomous trading workflow.

That means the target system is not just a chart viewer. The target system must:

- build and evolve its own strategy logic
- decide entries by itself
- decide exits by itself
- decide stop-loss placement by itself
- decide take-profit placement by itself
- use the chart as an inspection and explanation surface for those decisions

Design implication:

- strategy decisions are primary
- chart rendering is secondary
- chart overlays must reflect system decisions, not replace them

## Selected Chart Stack

Chosen option:

- `TradingView Lightweight Charts`

Why this is the current selection:

- lightweight enough for fast R&D
- good fit for candlestick chart display
- suitable for custom entry and exit markers
- suitable for stop-loss and take-profit horizontal levels
- easier to integrate into the existing FastAPI dashboard path than a heavier
  platform-style chart solution

What we expect to use it for in this project:

- render OHLC candles from our market feed
- show entry markers
- show exit markers
- show stop-loss and take-profit price lines
- visualize autonomous strategy decisions made by the system
- later add simple indicator overlays only as needed

What we are not assuming yet:

- no direct broker integration through the chart
- no advanced drawing-tool parity target
- no attempt to clone the full TradingView terminal workflow

## Current Baseline

The existing codebase already provides a partial foundation:

- `main.py` fetches ticker, orderbook, and candlestick data
- `signals/technical.py` generates technical indicator values
- `strategy/signal_strategy.py` decides when a signal may enter or exit
- `risk/stop_loss.py` calculates stop-loss and take-profit levels

What is still missing is a clean end-to-end workflow that treats chart review,
entry rules, exit rules, profit targets, and stop-loss logic as one consistent
trading path.

It also needs a stronger decision layer so the system can act from its own
rules and not depend on manual chart interpretation.

## RND Working Rule

Each step below should first be explored in `RND/`:

- notes go in `RND/docs/`
- validation scripts go in `RND/scripts/`
- prototype logic goes in `RND/experiments/`
- promotion notes go in `RND/patches/`

Only after a step is validated should it be moved into production modules.

## Step-by-Step Plan

### Step 1: Chart Access Foundation

Goal:
Create a reliable chart-data workflow for the symbols and timeframes we want to
trade.

Deliverables:

- define the primary symbol set for R&D
- define the primary timeframe set such as `5m`, `15m`, `1h`, `4h`
- verify candle schema consistency: timestamp, open, high, low, close, volume
- decide the minimum candle history required for indicators and trade review
- create a small R&D script that fetches and prints chart snapshots cleanly
- define the Lightweight Charts data shape we need for candlestick rendering
- define the marker and line payloads needed for entry, exit, SL, and TP

RND output:

- `RND/docs/chart-data-requirements.md`
- `RND/scripts/chart_snapshot.py`
- `RND/docs/lightweight-charts-integration-notes.md`

Promotion criteria:

- chart fetch is reliable
- timeframes are explicit
- indicator inputs are complete and stable

### Step 2: Entry Setup Definition

Goal:
Define exactly what a valid entry means on the chart.

Important clarification:
the chart does not decide the trade. The strategy engine decides the trade, and
the chart shows why the strategy decided it.

Deliverables:

- list entry setups to test first
- define confirmation rules for long and short entries
- define invalidation conditions before order placement
- define whether entries are market, limit, or simulated close-of-candle entries
- define whether entries require one timeframe or multi-timeframe confirmation
- define the machine-readable decision output for an autonomous entry decision

First candidate entry model:

- use the existing technical signal output as the base trigger
- require candle-close confirmation before entry
- reject weak entries when signal strength is below threshold
- reject entries that conflict with sentiment or extreme RSI states
- produce a structured reason set that can later be rendered on the chart

RND output:

- `RND/docs/entry-rules.md`
- optional prototype in `RND/experiments/entry_validator.py`

Promotion criteria:

- entry rules are deterministic
- no ambiguous discretionary language remains
- inputs needed by the strategy are available from chart data
- the output can be consumed by both execution logic and chart overlays

### Step 3: Stop-Loss Design

Goal:
Choose one initial stop-loss method for practical testing instead of mixing too
many variants at once.

Important clarification:
stop-loss values must be selected by the strategy and risk logic, then passed to
the chart for visibility.

Recommended first implementation:

- start with one primary stop model
- prefer `FIXED_PERCENT` or `ATR` first because both already align with existing
  code structure

Deliverables:

- define stop-loss placement rule for long trades
- define stop-loss placement rule for short trades
- define when trailing stop logic is allowed
- define stop movement rules after entry
- define risk per trade assumptions

RND output:

- `RND/docs/stop-loss-plan.md`
- optional validation helper in `RND/scripts/stop_loss_scenarios.py`

Promotion criteria:

- stop placement can be explained from chart structure or volatility
- stop distance is compatible with position sizing
- stop logic does not conflict with the selected entry style
- stop-loss output is machine-usable by both execution and visualization layers

### Step 4: Take-Profit and Exit Logic

Goal:
Separate profitable exit logic from defensive stop-loss logic.

Important clarification:
exit rules must be system-driven and testable without looking at the chart UI.

Deliverables:

- define fixed target vs staged target vs trailing target
- define early-exit conditions on reverse signal
- define whether exits happen intrabar or only on candle close
- define how partial exits will be handled, if at all
- define maximum holding duration for the R&D phase if needed

Recommended first version:

- one stop-loss
- one take-profit
- one reverse-signal exit rule

RND output:

- `RND/docs/exit-rules.md`
- optional prototype in `RND/experiments/exit_decision_flow.py`

Promotion criteria:

- exit precedence is clear
- stop-loss, take-profit, and reverse-signal rules do not overlap ambiguously
- exits can be backtested with current historical candles
- exit decisions can be emitted as structured autonomous signals

### Step 5: Trade Lifecycle Simulation

Goal:
Test the full path from chart snapshot to entry, stop-loss, take-profit, and
exit decision without changing production runtime yet.

Deliverables:

- create a small end-to-end R&D runner
- feed candles into signal generation
- produce an entry decision
- attach stop-loss and take-profit values
- simulate exit checks across subsequent candles
- emit a structured decision record that the chart can display directly

RND output:

- `RND/experiments/chart_trade_flow.py`
- `RND/docs/trade-lifecycle-observations.md`

Promotion criteria:

- the flow runs end to end without manual intervention
- logs are readable enough to explain every decision
- at least a few sample scenarios produce expected outcomes
- the same decision output can drive both execution and chart annotations

### Step 6: Promotion into Main Application

Goal:
Move the validated path into production modules with minimal ambiguity.

Likely production touchpoints:

- `main.py`
- `strategy/signal_strategy.py`
- `risk/stop_loss.py`
- possibly `execution/` if order simulation needs refinement

Deliverables:

- write a short promotion checklist
- identify exact files to update
- move only validated logic out of `RND/`
- keep a short patch note describing what was promoted

RND output:

- `RND/patches/chart-entry-exit-promotion.md`

Promotion criteria:

- behavior is reproducible from R&D artifacts
- defaults are documented
- test coverage is added for the promoted path

## Implementation Order

Recommended order for the next sessions:

1. Chart access foundation
2. Entry setup definition
3. Stop-loss design
4. Take-profit and exit logic
5. Trade lifecycle simulation
6. Production promotion

## Immediate Next Task

Start with Step 1 only.

Concrete next action:

- create one R&D script that fetches chart candles for a chosen symbol and
  timeframe
- log the most recent candles and confirm the data shape needed for entry/exit
  experiments
- map candle output into the future Lightweight Charts candlestick format

Follow-up direction after that:

- define a structured strategy decision payload before building richer chart UI

## Decision Boundaries for This Track

To keep this manageable, avoid these until the first workflow is stable:

- multiple strategy families at once
- partial profit-taking
- multi-broker live execution changes
- advanced UI/dashboard changes
- too many stop-loss variants in parallel

The first milestone is not “perfect trading logic.” The first milestone is a
clear, testable chart-to-trade workflow.

The second milestone is an autonomous strategy decision workflow that the chart
can explain visually.
