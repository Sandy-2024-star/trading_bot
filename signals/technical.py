"""
Technical indicators for trading signal generation.

Implements:
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- Moving Averages (SMA, EMA)
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Any, Optional
from loguru import logger


class TechnicalIndicators:
    """
    Calculate technical indicators from OHLCV data.
    """

    @staticmethod
    def calculate_rsi(data: pd.DataFrame, period: int = 14, column: str = "close") -> pd.Series:
        """
        Calculate Relative Strength Index (RSI).

        Args:
            data: DataFrame with price data
            period: RSI period (default 14)
            column: Price column to use

        Returns:
            Series with RSI values (0-100)
        """
        try:
            delta = data[column].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            logger.debug(f"RSI calculated with period={period}")
            return rsi

        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return pd.Series()

    @staticmethod
    def calculate_macd(
        data: pd.DataFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        column: str = "close"
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence).

        Args:
            data: DataFrame with price data
            fast_period: Fast EMA period (default 12)
            slow_period: Slow EMA period (default 26)
            signal_period: Signal line period (default 9)
            column: Price column to use

        Returns:
            Tuple of (macd_line, signal_line, histogram)
        """
        try:
            ema_fast = data[column].ewm(span=fast_period, adjust=False).mean()
            ema_slow = data[column].ewm(span=slow_period, adjust=False).mean()

            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
            histogram = macd_line - signal_line

            logger.debug(f"MACD calculated with periods {fast_period}/{slow_period}/{signal_period}")
            return macd_line, signal_line, histogram

        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            return pd.Series(), pd.Series(), pd.Series()

    @staticmethod
    def calculate_bollinger_bands(
        data: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0,
        column: str = "close"
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands.

        Args:
            data: DataFrame with price data
            period: Moving average period (default 20)
            std_dev: Number of standard deviations (default 2.0)
            column: Price column to use

        Returns:
            Tuple of (middle_band, upper_band, lower_band)
        """
        try:
            middle_band = data[column].rolling(window=period).mean()
            std = data[column].rolling(window=period).std()

            upper_band = middle_band + (std * std_dev)
            lower_band = middle_band - (std * std_dev)

            logger.debug(f"Bollinger Bands calculated with period={period}, std_dev={std_dev}")
            return middle_band, upper_band, lower_band

        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {e}")
            return pd.Series(), pd.Series(), pd.Series()

    @staticmethod
    def calculate_sma(data: pd.DataFrame, period: int = 20, column: str = "close") -> pd.Series:
        """
        Calculate Simple Moving Average (SMA).

        Args:
            data: DataFrame with price data
            period: Moving average period
            column: Price column to use

        Returns:
            Series with SMA values
        """
        try:
            sma = data[column].rolling(window=period).mean()
            logger.debug(f"SMA calculated with period={period}")
            return sma

        except Exception as e:
            logger.error(f"Error calculating SMA: {e}")
            return pd.Series()

    @staticmethod
    def calculate_ema(data: pd.DataFrame, period: int = 20, column: str = "close") -> pd.Series:
        """
        Calculate Exponential Moving Average (EMA).

        Args:
            data: DataFrame with price data
            period: Moving average period
            column: Price column to use

        Returns:
            Series with EMA values
        """
        try:
            ema = data[column].ewm(span=period, adjust=False).mean()
            logger.debug(f"EMA calculated with period={period}")
            return ema

        except Exception as e:
            logger.error(f"Error calculating EMA: {e}")
            return pd.Series()

    @staticmethod
    def calculate_vwap(data: pd.DataFrame) -> pd.Series:
        """
        Calculate Volume Weighted Average Price (VWAP).
        """
        try:
            if 'volume' not in data.columns or data['volume'].sum() == 0:
                return data['close'] # Fallback
                
            # Typical Price
            tp = (data['high'] + data['low'] + data['close']) / 3
            # Volume-Price Cumulative
            v_p_cum = (tp * data['volume']).cumsum()
            # Volume Cumulative
            vol_cum = data['volume'].cumsum()
            
            vwap = v_p_cum / vol_cum
            return vwap
        except Exception as e:
            logger.error(f"Error calculating VWAP: {e}")
            return data['close']

    @staticmethod
    def calculate_volume_profile(data: pd.DataFrame, bins: int = 10) -> Dict[str, Any]:
        """
        Calculate simple Volume Profile.
        Returns the Point of Control (POC) - price bin with highest volume.
        """
        try:
            if data.empty or 'volume' not in data.columns: return {}
            
            # Create bins
            min_p = data['low'].min()
            max_p = data['high'].max()
            if min_p == max_p: return {"poc": min_p, "profile": {}}
            
            price_bins = np.linspace(min_p, max_p, bins + 1)
            
            # Aggregate volume into bins
            labels = price_bins[:-1] + (price_bins[1] - price_bins[0]) / 2
            
            # Create a copy to avoid SettingWithCopyWarning
            df_bins = data.copy()
            df_bins['bin'] = pd.cut(df_bins['close'], bins=price_bins, labels=labels)
            
            profile = df_bins.groupby('bin', observed=True)['volume'].sum()
            poc = float(profile.idxmax()) if not profile.empty else 0.0
            
            return {
                "poc": poc,
                "profile": profile.to_dict()
            }
        except Exception as e:
            logger.error(f"Error calculating Volume Profile: {e}")
            return {}

    @staticmethod
    def calculate_ichimoku(
        data: pd.DataFrame,
        tenkan_period: int = 9,
        kijun_period: int = 26,
        senkou_b_period: int = 52,
        displacement: int = 26
    ) -> Dict[str, pd.Series]:
        """
        Calculate Ichimoku Cloud components.
        """
        try:
            # Tenkan-sen (Conversion Line): (9-period high + 9-period low) / 2
            tenkan_high = data['high'].rolling(window=tenkan_period).max()
            tenkan_low = data['low'].rolling(window=tenkan_period).min()
            tenkan_sen = (tenkan_high + tenkan_low) / 2

            # Kijun-sen (Base Line): (26-period high + 26-period low) / 2
            kijun_high = data['high'].rolling(window=kijun_period).max()
            kijun_low = data['low'].rolling(window=kijun_period).min()
            kijun_sen = (kijun_high + kijun_low) / 2

            # Senkou Span A (Leading Span A): (Conversion Line + Base Line) / 2
            senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(displacement)

            # Senkou Span B (Leading Span B): (52-period high + 52-period low) / 2
            senkou_high = data['high'].rolling(window=senkou_b_period).max()
            senkou_low = data['low'].rolling(window=senkou_b_period).min()
            senkou_span_b = ((senkou_high + senkou_low) / 2).shift(displacement)

            # Chikou Span (Lagging Span): Close plotted 26 days in the past
            chikou_span = data['close'].shift(-displacement)

            return {
                "tenkan_sen": tenkan_sen,
                "kijun_sen": kijun_sen,
                "senkou_span_a": senkou_span_a,
                "senkou_span_b": senkou_span_b,
                "chikou_span": chikou_span
            }
        except Exception as e:
            logger.error(f"Error calculating Ichimoku: {e}")
            return {}

    @staticmethod
    def calculate_fibonacci_retracement(data: pd.DataFrame, lookback: int = 50) -> Dict[str, float]:
        """
        Calculate Fibonacci Retracement levels for the recent range.
        """
        try:
            recent_data = data.tail(lookback)
            max_price = recent_data['high'].max()
            min_price = recent_data['low'].min()
            diff = max_price - min_price

            return {
                "level_0": max_price,
                "level_236": max_price - 0.236 * diff,
                "level_382": max_price - 0.382 * diff,
                "level_500": max_price - 0.5 * diff,
                "level_618": max_price - 0.618 * diff,
                "level_786": max_price - 0.786 * diff,
                "level_100": min_price
            }
        except Exception as e:
            logger.error(f"Error calculating Fibonacci: {e}")
            return {}

    @staticmethod
    def generate_signals(data: pd.DataFrame, params: Optional[Dict] = None) -> pd.DataFrame:
        """
        Generate trading signals based on multiple technical indicators.

        Args:
            data: DataFrame with OHLCV data
            params: Optional dictionary of indicator parameters:
                - rsi_period: default 14
                - rsi_oversold: default 30
                - rsi_overbought: default 70
                - macd_fast: default 12
                - macd_slow: default 26
                - macd_signal: default 9
                - bb_period: default 20
                - bb_std: default 2.0
                - sma_fast: default 20
                - sma_slow: default 50

        Returns:
            DataFrame with added indicator columns and signal strength
        """
        try:
            df = data.copy()
            p = params or {}

            # RSI
            rsi_period = p.get("rsi_period", 14)
            rsi_oversold = p.get("rsi_oversold", 30)
            rsi_overbought = p.get("rsi_overbought", 70)
            df["rsi"] = TechnicalIndicators.calculate_rsi(df, period=rsi_period)

            # MACD
            macd_fast = p.get("macd_fast", 12)
            macd_slow = p.get("macd_slow", 26)
            macd_signal = p.get("macd_signal", 9)
            df["macd"], df["macd_signal"], df["macd_hist"] = TechnicalIndicators.calculate_macd(
                df, fast_period=macd_fast, slow_period=macd_slow, signal_period=macd_signal
            )

            # Bollinger Bands
            bb_period = p.get("bb_period", 20)
            bb_std = p.get("bb_std", 2.0)
            df["bb_middle"], df["bb_upper"], df["bb_lower"] = TechnicalIndicators.calculate_bollinger_bands(
                df, period=bb_period, std_dev=bb_std
            )

            # Moving Averages
            sma_fast = p.get("sma_fast", 20)
            sma_slow = p.get("sma_slow", 50)
            df["sma_fast"] = TechnicalIndicators.calculate_sma(df, period=sma_fast)
            df["sma_slow"] = TechnicalIndicators.calculate_sma(df, period=sma_slow)

            # Ichimoku
            ichimoku = TechnicalIndicators.calculate_ichimoku(df)
            for name, series in ichimoku.items():
                df[name] = series

            # Fibonacci (last value only for latest signal)
            fib = TechnicalIndicators.calculate_fibonacci_retracement(df)
            for name, val in fib.items():
                df[f"fib_{name}"] = val

            # VWAP
            df["vwap"] = TechnicalIndicators.calculate_vwap(df)

            # Volume Profile POC
            vp = TechnicalIndicators.calculate_volume_profile(df)
            df["poc"] = vp.get("poc", 0.0)

            # Generate signal scores (-1 to 1, where -1 = strong sell, 1 = strong buy)
            signal_score = 0

            # RSI signals
            if not df["rsi"].empty:
                rsi_last = df["rsi"].iloc[-1]
                if rsi_last < rsi_oversold:
                    signal_score += 0.5  # Oversold
                elif rsi_last > rsi_overbought:
                    signal_score -= 0.5  # Overbought

            # MACD signals
            if not df["macd_hist"].empty:
                macd_hist_last = df["macd_hist"].iloc[-1]
                macd_hist_prev = df["macd_hist"].iloc[-2] if len(df) > 1 else 0
                if macd_hist_last > 0 and macd_hist_prev <= 0:
                    signal_score += 0.3  # Bullish crossover
                elif macd_hist_last < 0 and macd_hist_prev >= 0:
                    signal_score -= 0.3  # Bearish crossover

            # Bollinger Bands signals
            if not df["bb_lower"].empty:
                close_last = df["close"].iloc[-1]
                bb_upper_last = df["bb_upper"].iloc[-1]
                bb_lower_last = df["bb_lower"].iloc[-1]
                if close_last < bb_lower_last:
                    signal_score += 0.2  # Below lower band
                elif close_last > bb_upper_last:
                    signal_score -= 0.2  # Above upper band

            # Ichimoku signals
            if "senkou_span_a" in df.columns and "senkou_span_b" in df.columns:
                span_a = df["senkou_span_a"].iloc[-1]
                span_b = df["senkou_span_b"].iloc[-1]
                tenkan = df["tenkan_sen"].iloc[-1]
                kijun = df["kijun_sen"].iloc[-1]
                
                # Trend: Price relative to Cloud
                if close_last > max(span_a, span_b):
                    signal_score += 0.2  # Bullish trend
                elif close_last < min(span_a, span_b):
                    signal_score -= 0.2  # Bearish trend
                    
                # Crossover: Tenkan vs Kijun
                if tenkan > kijun:
                    signal_score += 0.1
                elif tenkan < kijun:
                    signal_score -= 0.1

            df["signal_score"] = signal_score

            # Signal interpretation
            if signal_score > 0.5:
                df["signal"] = "STRONG_BUY"
            elif signal_score > 0:
                df["signal"] = "BUY"
            elif signal_score < -0.5:
                df["signal"] = "STRONG_SELL"
            elif signal_score < 0:
                df["signal"] = "SELL"
            else:
                df["signal"] = "HOLD"

            logger.debug(f"Generated signal: {df['signal'].iloc[-1]} (score: {signal_score:.2f})")
            return df

        except Exception as e:
            logger.error(f"Error generating signals: {e}")
            return data


# Example usage
def main():
    # Sample data
    sample_data = pd.DataFrame({
        "timestamp": pd.date_range(start="2024-01-01", periods=100, freq="1h"),
        "open": np.random.randn(100).cumsum() + 100,
        "high": np.random.randn(100).cumsum() + 102,
        "low": np.random.randn(100).cumsum() + 98,
        "close": np.random.randn(100).cumsum() + 100,
        "volume": np.random.randint(1000, 10000, 100)
    })

    indicators = TechnicalIndicators()

    # Calculate individual indicators
    rsi = indicators.calculate_rsi(sample_data)
    print(f"RSI (last 5): {rsi.tail()}")

    macd, signal, hist = indicators.calculate_macd(sample_data)
    print(f"\nMACD (last 5): {macd.tail()}")

    middle, upper, lower = indicators.calculate_bollinger_bands(sample_data)
    print(f"\nBollinger Bands middle (last 5): {middle.tail()}")

    # Generate combined signals
    signals_df = indicators.generate_signals(sample_data)
    print(f"\nLast signal: {signals_df[['timestamp', 'close', 'rsi', 'signal', 'signal_score']].tail()}")


if __name__ == "__main__":
    main()
