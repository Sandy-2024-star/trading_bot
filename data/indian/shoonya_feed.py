"""
Shoonya (Finvasia) market data adapter for free Indian market data.
"""

import asyncio
from typing import Optional, List, Dict
import pandas as pd
from datetime import datetime
from loguru import logger
import pyotp
from NorenRestApiPy.NorenApi import NorenApi

from core.base_feed import MarketDataFeed
from data.market_cache import market_cache
from config.config import config
from utils.options_quant import calculate_greeks

class ShoonyaApi(NorenApi):
    """Custom wrapper for NorenApi to handle login logic."""
    def __init__(self):
        NorenApi.__init__(self, host='https://api.shoonya.com/NorenWSTP/', websocket='wss://api.shoonya.com/NorenWSTP/')

class ShoonyaFeed(MarketDataFeed):
    """
    Shoonya API connector for market data.
    Provides free real-time and historical data for NSE, BSE, and MCX.
    """

    def __init__(self):
        self.api = ShoonyaApi()
        self.cache = market_cache
        self.logged_in = False
        logger.info("ShoonyaFeed initialized")

    async def connect(self):
        """Establish connection and login to Shoonya."""
        if self.logged_in:
            return True

        if not all([config.SHOONYA_USER_ID, config.SHOONYA_PASSWORD, config.SHOONYA_API_KEY, config.SHOONYA_TOTP_SECRET]):
            logger.error("Shoonya credentials incomplete in .env")
            return False

        try:
            # Generate TOTP
            totp = pyotp.TOTP(config.SHOONYA_TOTP_SECRET).now()
            
            # Perform login (synchronous SDK call)
            login_resp = await asyncio.to_thread(
                self.api.login,
                userid=config.SHOONYA_USER_ID,
                password=config.SHOONYA_PASSWORD,
                twoFA=totp,
                vendor_code=config.SHOONYA_VENDOR_CODE,
                api_secret=config.SHOONYA_API_KEY,
                imei=config.SHOONYA_IMEI
            )

            if login_resp and login_resp.get('stat') == 'Ok':
                self.logged_in = True
                logger.info("Successfully logged into Shoonya")
                return True
            else:
                logger.error(f"Shoonya login failed: {login_resp}")
                return False
        except Exception as e:
            logger.error(f"Error connecting to Shoonya: {e}")
            return False

    async def close(self):
        """No-op for Shoonya REST API."""
        pass

    def _normalize_symbol(self, symbol: str) -> str:
        """
        Map common symbols to Shoonya format (Exchange|Symbol).
        Example: RELIANCE -> NSE|RELIANCE
        """
        upper = symbol.strip().upper()
        if "|" in upper:
            return upper
            
        # Default to NSE for stocks, MCX for commodities
        if any(c in upper for c in ["GOLD", "SILVER", "CRUDE"]):
            return f"MCX|{upper}"
        
        return f"NSE|{upper}"

    async def get_ticker(self, symbol: str) -> Optional[Dict]:
        """Fetch a spot price snapshot."""
        if not self.logged_in:
            await self.connect()

        # Check cache
        cached = self.cache.get_ticker(symbol)
        if cached:
            return cached

        sh_symbol = self._normalize_symbol(symbol)
        exch, token_symbol = sh_symbol.split('|')

        try:
            # Shoonya get_quotes expects exchange and symbol
            # Note: Shoonya often needs a numeric token for many calls, 
            # but search_scrip can find it.
            quotes = await asyncio.to_thread(self.api.get_quotes, exchange=exch, token=token_symbol)
            
            if quotes and quotes.get('stat') == 'Ok':
                data = {
                    "symbol": symbol,
                    "last_price": float(quotes.get('lp', 0)),
                    "volume_24h": float(quotes.get('v', 0)),
                    "high_24h": float(quotes.get('h', 0)),
                    "low_24h": float(quotes.get('l', 0)),
                    "timestamp": datetime.now(),
                    "provider": "shoonya"
                }
                self.cache.set_ticker(symbol, data, expire=5)
                return data
            return None
        except Exception as e:
            logger.error(f"Error fetching Shoonya ticker for {symbol}: {e}")
            return None

    async def get_candlesticks(
        self, 
        symbol: str, 
        timeframe: str = "1h", 
        limit: int = 100
    ) -> pd.DataFrame:
        """Fetch historical OHLCV data."""
        if not self.logged_in:
            await self.connect()

        # Check cache
        cached_df = self.cache.get_candlesticks(symbol, timeframe)
        if cached_df is not None and not cached_df.empty:
            return cached_df

        sh_symbol = self._normalize_symbol(symbol)
        exch, token_symbol = sh_symbol.split('|')

        # Map timeframes to Shoonya intervals (in minutes)
        # Shoonya supports: 1, 3, 5, 10, 15, 30, 60, 120, 240, D
        interval_map = {
            "1m": "1", "5m": "5", "15m": "15", 
            "1h": "60", "1D": "D"
        }
        interval = interval_map.get(timeframe, "60")

        try:
            # Get historical data
            # First, we might need to resolve the token ID for the symbol
            search = await asyncio.to_thread(self.api.search_scrip, exchange=exch, searchtext=token_symbol)
            if not search or not search.get('values'):
                return pd.DataFrame()
            
            token = search['values'][0]['token']
            
            # Calculate start time based on limit
            end_time = datetime.now()
            # Approximation
            start_time = end_time - pd.Timedelta(days=10) # 10 days for safety
            
            data = await asyncio.to_thread(
                self.api.get_time_price_series,
                exchange=exch,
                token=token,
                starttime=int(start_time.timestamp()),
                endtime=int(end_time.timestamp()),
                interval=interval
            )

            if not data or not isinstance(data, list):
                return pd.DataFrame()

            df = pd.DataFrame(data)
            # Shoonya format: time, ssclose, sshigh, sslow, ssopen, ssvolume
            df = df.rename(columns={
                'time': 'timestamp',
                'into': 'open',
                'inth': 'high',
                'intl': 'low',
                'intc': 'close',
                'intv': 'volume'
            })
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], format='%d-%m-%Y %H:%M:%S')
            
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
                
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            df = df.sort_values("timestamp").tail(limit)
            
            self.cache.set_candlesticks(symbol, timeframe, df, expire=300)
            return df
        except Exception as e:
            logger.error(f"Error fetching Shoonya candles for {symbol}: {e}")
            return pd.DataFrame()

    async def get_orderbook(self, symbol: str, depth: int = 10) -> Optional[Dict]:
        """Fetch orderbook depth."""
        # Shoonya provides depth via get_quotes or a dedicated market depth call
        return None

    async def get_option_chain(self, underlying: str, expiry: str) -> List[Dict]:
        """
        Fetch option chain for an underlying asset.
        Args:
            underlying: NSE|NIFTY or NSE|BANKNIFTY
            expiry: Date string (e.g. 25-APR-2024)
        """
        if not self.logged_in:
            await self.connect()

        try:
            exch, symbol = underlying.split('|')
            chain = await asyncio.to_thread(
                self.api.get_option_chain,
                exchange=exch,
                tradingsymbol=symbol,
                expiry=expiry
            )
            
            if chain and chain.get('stat') == 'Ok':
                return chain.get('values', [])
            return []
        except Exception as e:
            logger.error(f"Error fetching Shoonya option chain: {e}")
            return []

    async def get_greeks(
        self, 
        symbol: str, 
        spot_price: float, 
        expiry_date: datetime, 
        risk_free_rate: float = 0.07
    ) -> Dict:
        """
        Calculate live Greeks for a specific option symbol.
        """
        if not self.logged_in:
            await self.connect()

        try:
            # 1. Fetch live quote for IV and Price
            if "|" not in symbol:
                symbol = f"NFO|{symbol}"
            exch, token_symbol = symbol.split('|')
            quotes = await asyncio.to_thread(self.api.get_quotes, exchange=exch, token=token_symbol)
            
            if not quotes or quotes.get('stat') != 'Ok':
                return {}

            # 2. Extract inputs for BS model
            strike = float(quotes.get('strprc', 0))
            option_type = 'call' if quotes.get('optt') == 'CE' else 'put'
            iv = float(quotes.get('iv', 0)) / 100 # Shoonya provides IV in %
            
            # Time to expiry in years
            now = datetime.now()
            diff = expiry_date - now
            days_to_expiry = diff.days + diff.seconds / 86400
            T = max(0, days_to_expiry / 365)

            # 3. Calculate Greeks
            greeks = calculate_greeks(
                S=spot_price,
                K=strike,
                T=T,
                r=risk_free_rate,
                sigma=iv,
                option_type=option_type
            )
            
            return {
                "symbol": symbol,
                "strike": strike,
                "type": option_type,
                "iv": iv,
                "days_to_expiry": days_to_expiry,
                **greeks
            }
        except Exception as e:
            logger.error(f"Error calculating Shoonya Greeks for {symbol}: {e}")
            return {}
