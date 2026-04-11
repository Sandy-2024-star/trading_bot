"""
R&D utility for fetching chart candles and converting them into
TradingView Lightweight Charts payloads.

Run from `trading_bot/`:

    python RND/scripts/chart_snapshot.py
    python RND/scripts/chart_snapshot.py --symbol ETHUSD --timeframe 4h --limit 60
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List

try:
    from data.factory import create_market_data_feed
except ImportError:  # pragma: no cover - fallback when executed outside trading_bot/
    import sys

    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from data.factory import create_market_data_feed


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch chart candles and print Lightweight Charts payloads.",
    )
    parser.add_argument("--symbol", default="BTCUSD", help="Trading pair such as BTCUSD or ETHUSD.")
    parser.add_argument("--timeframe", default="1h", help="Chart timeframe such as 5m, 15m, 1h, 4h.")
    parser.add_argument("--limit", type=int, default=100, help="Maximum candles to return.")
    parser.add_argument(
        "--provider",
        default=None,
        help="Optional market data provider override. Defaults to configured provider.",
    )
    return parser


def _to_lightweight_candles(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    payload = []
    for row in rows:
        timestamp = row["timestamp"]
        payload.append(
            {
                "time": int(timestamp.timestamp()),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
            }
        )
    return payload


def _build_reference_trade(candles: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not candles:
        return {
            "markers": [],
            "price_lines": [],
        }

    entry_candle = candles[max(len(candles) - 3, 0)]
    exit_candle = candles[-1]
    entry_price = entry_candle["close"]
    stop_loss = round(entry_price * 0.97, 2)
    take_profit = round(entry_price * 1.05, 2)

    return {
        "markers": [
            {
                "time": entry_candle["time"],
                "position": "belowBar",
                "color": "#26a69a",
                "shape": "arrowUp",
                "text": f"Entry {entry_price:.2f}",
            },
            {
                "time": exit_candle["time"],
                "position": "aboveBar",
                "color": "#ef5350",
                "shape": "arrowDown",
                "text": f"Exit {exit_candle['close']:.2f}",
            },
        ],
        "price_lines": [
            {
                "title": "Entry",
                "price": round(entry_price, 2),
                "color": "#2962ff",
                "lineStyle": "solid",
            },
            {
                "title": "SL",
                "price": stop_loss,
                "color": "#d32f2f",
                "lineStyle": "dashed",
            },
            {
                "title": "TP",
                "price": take_profit,
                "color": "#2e7d32",
                "lineStyle": "dashed",
            },
        ],
    }


async def _run(symbol: str, timeframe: str, limit: int, provider: str | None) -> None:
    feed = create_market_data_feed(provider)
    try:
        candles_df = await feed.get_candlesticks(symbol, timeframe=timeframe, limit=limit)
        if candles_df.empty:
            print(f"No candles returned for {symbol} {timeframe}")
            return

        records = candles_df.to_dict("records")
        chart_candles = _to_lightweight_candles(records)
        overlay_payload = _build_reference_trade(chart_candles)

        print("=== Snapshot Request ===")
        print(
            json.dumps(
                {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "requested_limit": limit,
                    "returned_candles": len(chart_candles),
                    "provider": provider or "configured_default",
                },
                indent=2,
            )
        )

        print("\n=== Candle Schema Check ===")
        print(
            json.dumps(
                {
                    "required_columns": list(candles_df.columns),
                    "latest_timestamp": records[-1]["timestamp"].isoformat(),
                    "latest_close": float(records[-1]["close"]),
                    "volume_supported": "volume" in candles_df.columns,
                },
                indent=2,
            )
        )

        print("\n=== Recent Candle Sample ===")
        print(
            json.dumps(
                chart_candles[-5:],
                indent=2,
            )
        )

        print("\n=== Lightweight Charts Overlay Sample ===")
        print(json.dumps(overlay_payload, indent=2))

    finally:
        await feed.close()


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    asyncio.run(
        _run(
            symbol=args.symbol,
            timeframe=args.timeframe,
            limit=args.limit,
            provider=args.provider,
        )
    )


if __name__ == "__main__":
    main()
