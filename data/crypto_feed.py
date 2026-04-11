"""
Crypto.com market data fetcher.
Provides real-time and historical market data for cryptocurrency trading.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
import pandas as pd
from loguru import logger
from core.base_feed import MarketDataFeed


class CryptoFeed(MarketDataFeed):
    """
    Crypto.com API connector for market data.

    Supports:
    - Real-time ticker data
    - Orderbook snapshots
    - Historical candlestick data (OHLCV)
    """

    BASE_URL = "https://api.crypto.com/exchange/v1/public"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self._resolved_symbols: Dict[str, str] = {}
        logger.info("CryptoFeed initialized")

    async def connect(self):
        """Establish connection (no-op for REST)."""
        pass

    async def close(self):
        """Close HTTP client connection."""
        await self.client.aclose()

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize caller-provided symbols to Crypto.com instrument style."""
        clean_symbol = symbol.strip().upper().replace("-", "_").replace("/", "_")
        if "_" in clean_symbol:
            return clean_symbol

        quote_candidates = ("USDT", "USDC", "USD", "BTC", "ETH")
        for quote in quote_candidates:
            if clean_symbol.endswith(quote) and len(clean_symbol) > len(quote):
                base = clean_symbol[:-len(quote)]
                return f"{base}_{quote}"

        return clean_symbol

    def _candidate_symbols(self, symbol: str) -> List[str]:
        """Generate likely Crypto.com instrument candidates for a requested symbol."""
        requested = symbol.strip().upper()
        candidates: List[str] = []

        for candidate in (
            self._resolved_symbols.get(requested),
            self._normalize_symbol(requested),
            requested,
        ):
            if candidate and candidate not in candidates:
                candidates.append(candidate)

        if requested == "BTCUSD":
            candidates.extend([c for c in ("BTC_USD", "BTC_USDT") if c not in candidates])
        elif requested == "ETHUSD":
            candidates.extend([c for c in ("ETH_USD", "ETH_USDT") if c not in candidates])

        return candidates

    async def _request(
        self,
        endpoint: str,
        symbol: str,
        extra_params: Optional[Dict[str, Any]] = None,
        retries: int = 2,
    ) -> Optional[Dict[str, Any]]:
        """Call a public endpoint, retrying transient failures and probing symbol variants."""
        params = dict(extra_params or {})
        last_error: Optional[Exception] = None

        for candidate in self._candidate_symbols(symbol):
            request_params = {**params, "instrument_name": candidate}

            for attempt in range(retries + 1):
                try:
                    response = await self.client.get(
                        f"{self.BASE_URL}/{endpoint}",
                        params=request_params,
                    )
                    response.raise_for_status()
                    data = response.json()

                    if data.get("code") == 0:
                        self._resolved_symbols[symbol.strip().upper()] = candidate
                        return data

                    logger.warning(
                        "Crypto.com returned application error for {} with {}: {}",
                        endpoint,
                        candidate,
                        data,
                    )
                    break
                except httpx.HTTPStatusError as exc:
                    last_error = exc
                    if exc.response.status_code == 400:
                        logger.warning(
                            "Rejected {} for {} on {}. Trying next candidate.",
                            candidate,
                            symbol,
                            endpoint,
                        )
                        break
                    if attempt == retries:
                        logger.error(
                            "HTTP error fetching {} for {} (candidate {}): {}",
                            endpoint,
                            symbol,
                            candidate,
                            exc,
                        )
                    else:
                        await asyncio.sleep(0.5 * (attempt + 1))
                except httpx.HTTPError as exc:
                    last_error = exc
                    if attempt == retries:
                        logger.error(
                            "Network error fetching {} for {} (candidate {}): {}",
                            endpoint,
                            symbol,
                            candidate,
                            exc,
                        )
                    else:
                        await asyncio.sleep(0.5 * (attempt + 1))

        if last_error:
            logger.error("Failed to fetch {} for {}: {}", endpoint, symbol, last_error)
        else:
            logger.error("No valid Crypto.com instrument found for {}", symbol)
        return None

    async def get_ticker(self, symbol: str = "BTCUSD") -> Dict:
        """
        Fetch real-time ticker data for a symbol.

        Args:
            symbol: Trading pair (e.g., BTCUSD, ETHUSD)

        Returns:
            Dict with keys: symbol, last_price, bid, ask, volume_24h, timestamp
        """
        try:
            data = await self._request("get-ticker", symbol)

            if data and "result" in data:
                result = data["result"]["data"][0]
                return {
                    "symbol": symbol,
                    "last_price": float(result.get("a", 0)),
                    "bid": float(result.get("b", 0)),
                    "ask": float(result.get("k", 0)),
                    "volume_24h": float(result.get("v", 0)),
                    "high_24h": float(result.get("h", 0)),
                    "low_24h": float(result.get("l", 0)),
                    "timestamp": datetime.now()
                }
            else:
                logger.error(f"API error: {data}")
                return {}

        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            return {}

    async def get_orderbook(self, symbol: str = "BTCUSD", depth: int = 10) -> Dict:
        """
        Fetch orderbook snapshot.

        Args:
            symbol: Trading pair
            depth: Number of price levels (default 10)

        Returns:
            Dict with keys: bids, asks, timestamp
        """
        try:
            data = await self._request("get-book", symbol, extra_params={"depth": depth})

            if data and "result" in data:
                result = data["result"]["data"][0]
                return {
                    "symbol": symbol,
                    "bids": [[float(b[0]), float(b[1])] for b in result.get("bids", [])],
                    "asks": [[float(a[0]), float(a[1])] for a in result.get("asks", [])],
                    "timestamp": datetime.now()
                }
            else:
                logger.error(f"API error: {data}")
                return {}

        except Exception as e:
            logger.error(f"Error fetching orderbook for {symbol}: {e}")
            return {}

    async def get_candlesticks(
        self,
        symbol: str = "BTCUSD",
        timeframe: str = "1h",
        limit: int = 100
    ) -> pd.DataFrame:
        """
        Fetch historical candlestick data.

        Args:
            symbol: Trading pair
            timeframe: Candle interval (1m, 5m, 15m, 1h, 4h, 1D)
            limit: Number of candles to fetch

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        try:
            timeframe_map = {
                "1m": "1m", "5m": "5m", "15m": "15m",
                "1h": "1h", "4h": "4h", "1D": "1D"
            }

            if timeframe not in timeframe_map:
                logger.error(f"Invalid timeframe: {timeframe}")
                return pd.DataFrame()

            data = await self._request(
                "get-candlestick",
                symbol,
                extra_params={"timeframe": timeframe_map[timeframe]},
            )

            if data and "result" in data:
                candles = data["result"]["data"]
                if not candles:
                    logger.warning(f"No candlestick data returned for {symbol}")
                    return pd.DataFrame()

                df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
                df[["open", "high", "low", "close", "volume"]] = df[
                    ["open", "high", "low", "close", "volume"]
                ].astype(float)

                df = df.sort_values("timestamp", ascending=False).head(limit)
                df = df.sort_values("timestamp").reset_index(drop=True)

                logger.info(f"Fetched {len(df)} candles for {symbol} ({timeframe})")
                return df
            else:
                logger.error(f"API error: {data}")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error fetching candlesticks for {symbol}: {e}")
            return pd.DataFrame()

    async def get_multiple_tickers(self, symbols: List[str]) -> List[Dict]:
        """
        Fetch ticker data for multiple symbols concurrently.

        Args:
            symbols: List of trading pairs

        Returns:
            List of ticker dicts
        """
        tasks = [self.get_ticker(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r]


# Example usage
async def main():
    feed = CryptoFeed()

    # Fetch ticker
    ticker = await feed.get_ticker("BTCUSD")
    print(f"Ticker: {ticker}")

    # Fetch orderbook
    orderbook = await feed.get_orderbook("BTCUSD", depth=5)
    print(f"\nOrderbook bids: {orderbook.get('bids', [])[:3]}")
    print(f"Orderbook asks: {orderbook.get('asks', [])[:3]}")

    # Fetch candlesticks
    candles = await feed.get_candlesticks("BTCUSD", timeframe="1h", limit=20)
    print(f"\nCandlesticks:\n{candles.tail()}")

    await feed.close()


if __name__ == "__main__":
    asyncio.run(main())
