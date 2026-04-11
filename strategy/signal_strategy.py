"""
Signal-based trading strategy.
Uses technical indicators to generate buy/sell signals.
"""

import pandas as pd
from typing import Optional, Dict, List, Union
from loguru import logger


from core.base_strategy import BaseStrategy, Signal, OrderSide, Position
from signals.technical import TechnicalIndicators
from ai.lstm_model import LSTMPricePredictor


class TechnicalSignalStrategy(BaseStrategy):
    """
    Strategy based on technical indicator signals.

    Entry conditions:
    - RSI < 30 (oversold) or RSI > 70 (overbought)
    - MACD histogram crossover
    - Price near Bollinger Bands
    - Signal strength threshold

    Exit conditions:
    - Stop loss hit
    - Take profit hit
    - Reverse signal
    """

    def __init__(
        self,
        name: str = "TechnicalSignalStrategy",
        signal_threshold: float = 0.5,
        use_stop_loss: bool = True,
        use_take_profit: bool = True,
        symbol_params: Optional[Dict[str, Dict]] = None
    ):
        super().__init__(name)
        self.signal_threshold = signal_threshold
        self.use_stop_loss = use_stop_loss
        self.use_take_profit = use_take_profit
        self.indicators = TechnicalIndicators()
        self.symbol_params = symbol_params or {}
        self.ai_predictors: Dict[str, LSTMPricePredictor] = {}

    def analyze(self, data: Union[pd.DataFrame, Dict[str, pd.DataFrame]]) -> Optional[Signal]:
        """
        Analyze market data and generate trading signal.
        Supports multi-timeframe analysis if a dictionary is provided.
        """
        try:
            # 1. Handle Multi-Timeframe input
            if isinstance(data, dict):
                # Identify timeframes
                available_tfs = sorted(data.keys(), key=lambda x: self._tf_to_minutes(x))
                if not available_tfs:
                    return None
                
                # Primary timeframe for entry (the lowest one provided)
                primary_tf = available_tfs[0]
                primary_data = data[primary_tf]
                other_data = {tf: df for tf, df in data.items() if tf != primary_tf}
            else:
                primary_data = data
                other_data = {}

            # 2. Get symbol and params
            symbol = primary_data.get("symbol", "UNKNOWN")
            if isinstance(symbol, pd.Series):
                symbol = symbol.iloc[0]
                
            params = self.symbol_params.get(symbol, {})
            
            # 3. Generate primary indicators and signal
            df = self.indicators.generate_signals(primary_data, params=params)

            if df.empty or len(df) < 2:
                return None

            latest = df.iloc[-1]
            market_context = self.get_market_context(symbol)

            # 4. Multi-Timeframe Trend Confirmation
            mtf_bias = 0 # -1 to 1
            for tf, tf_df in other_data.items():
                # Generate simple trend indicators for higher timeframes
                tf_indicators = self.indicators.generate_signals(tf_df, params=params)
                if not tf_indicators.empty:
                    tf_latest = tf_indicators.iloc[-1]
                    # Score based on SMA crossover and Ichimoku
                    if tf_latest.get('sma_fast', 0) > tf_latest.get('sma_slow', 0):
                        mtf_bias += 0.5
                    else:
                        mtf_bias -= 0.5
                    
                    # Ichimoku check
                    if tf_latest.get('tenkan_sen', 0) > tf_latest.get('kijun_sen', 0):
                        mtf_bias += 0.5
                    else:
                        mtf_bias -= 0.5

            # Normalize MTF bias
            mtf_bias = max(-1.0, min(1.0, mtf_bias / max(1, len(other_data)))) if other_data else 0

            # 5. Combine with Sentiment and AI
            if symbol not in self.ai_predictors:
                self.ai_predictors[symbol] = LSTMPricePredictor(symbol)
            
            ai_score = self.ai_predictors[symbol].predict_direction(primary_data)
            # Normalize AI score to -1.0 to 1.0 range (sigmoid 0.5 is neutral)
            ai_bias = (ai_score - 0.5) * 2

            # Extract signal information
            signal_str = latest.get("signal", "HOLD")
            signal_score = latest.get("signal_score", 0.0)
            sentiment_score = float(market_context.get("sentiment_score", 0.0) or 0.0)
            
            # Combine signals: Technical (40%) + Sentiment (25%) + AI (15%) + MTF Trend (20%)
            adjusted_signal_score = (signal_score * 0.4) + (sentiment_score * 0.25) + (ai_bias * 0.15) + (mtf_bias * 0.2)

            # Determine order side
            if "BUY" in signal_str and adjusted_signal_score > 0:
                side = OrderSide.BUY
                strength = min(abs(adjusted_signal_score), 1.0)
            elif "SELL" in signal_str and adjusted_signal_score < 0:
                side = OrderSide.SELL
                strength = min(abs(adjusted_signal_score), 1.0)
            else:
                self.record_latest_signal(symbol, None)
                return None  # HOLD signal

            # Create signal with indicator values
            signal = Signal(
                symbol=symbol,
                side=side,
                strength=strength,
                indicators={
                    "rsi": latest.get("rsi"),
                    "macd": latest.get("macd"),
                    "macd_signal": latest.get("macd_signal"),
                    "macd_hist": latest.get("macd_hist"),
                    "bb_upper": latest.get("bb_upper"),
                    "bb_middle": latest.get("bb_middle"),
                    "bb_lower": latest.get("bb_lower"),
                    "tenkan_sen": latest.get("tenkan_sen"),
                    "kijun_sen": latest.get("kijun_sen"),
                    "senkou_span_a": latest.get("senkou_span_a"),
                    "senkou_span_b": latest.get("senkou_span_b"),
                    "vwap": latest.get("vwap"),
                    "poc": latest.get("poc"),
                    "fib_level_382": latest.get("fib_level_382"),
                    "fib_level_500": latest.get("fib_level_500"),
                    "fib_level_618": latest.get("fib_level_618"),
                    "sma_20": latest.get("sma_20"),
                    "sma_50": latest.get("sma_50"),
                    "close": latest.get("close"),
                    "base_signal_score": signal_score,
                    "sentiment_score": sentiment_score,
                    "sentiment_label": market_context.get("sentiment_label", "NEUTRAL"),
                    "article_count": market_context.get("article_count", 0),
                    "eurusd_rate": market_context.get("eurusd_rate"),
                    "news_provider": market_context.get("news_provider"),
                    "forex_provider": market_context.get("forex_provider"),
                    "ai_score": ai_score,
                    "ai_bias": ai_bias,
                    "mtf_bias": mtf_bias,
                }
            )

            self.record_latest_signal(symbol, signal)
            logger.info(f"Signal generated: {signal}")
            return signal

        except Exception as e:
            logger.error(f"Error analyzing data: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def _tf_to_minutes(self, tf: str) -> int:
        """Helper to convert timeframe string to minutes for sorting."""
        unit = tf[-1].lower()
        try:
            val = int(tf[:-1])
            if unit == 'm': return val
            if unit == 'h': return val * 60
            if unit == 'd': return val * 1440
        except:
            pass
        return 0

    def should_enter(self, signal: Signal, current_price: float, account_balance: float) -> bool:
        """
        Determine if we should enter a position based on the signal.

        Args:
            signal: Trading signal
            current_price: Current market price
            account_balance: Available account balance

        Returns:
            True if should enter, False otherwise
        """
        # Check signal strength threshold
        if abs(signal.strength) < self.signal_threshold:
            logger.debug(f"Signal strength {signal.strength:.2f} below threshold {self.signal_threshold}")
            return False

        # Check if we have sufficient balance
        min_position_value = 100  # Minimum $100 position
        if account_balance < min_position_value:
            logger.warning(f"Insufficient balance: ${account_balance:.2f}")
            return False

        # Check if we already have an open position in this symbol
        open_positions = self.get_open_positions(signal.symbol)
        if open_positions:
            logger.debug(f"Already have open position in {signal.symbol}")
            return False

        # Additional checks based on indicators
        rsi = signal.indicators.get("rsi")
        if rsi:
            # Don't buy if extremely overbought
            if signal.side == OrderSide.BUY and rsi > 80:
                logger.debug(f"RSI too high for buy: {rsi:.2f}")
                return False
            # Don't sell if extremely oversold
            if signal.side == OrderSide.SELL and rsi < 20:
                logger.debug(f"RSI too low for sell: {rsi:.2f}")
                return False

        sentiment_score = float(signal.indicators.get("sentiment_score", 0.0) or 0.0)
        if signal.side == OrderSide.BUY and sentiment_score <= -0.35:
            logger.info(f"Skipping buy for {signal.symbol} due to bearish sentiment {sentiment_score:.2f}")
            return False
        if signal.side == OrderSide.SELL and sentiment_score >= 0.35:
            logger.info(f"Skipping sell for {signal.symbol} due to bullish sentiment {sentiment_score:.2f}")
            return False

        # Ichimoku Trend Filter
        span_a = signal.indicators.get("senkou_span_a")
        span_b = signal.indicators.get("senkou_span_b")
        if span_a and span_b:
            cloud_top = max(span_a, span_b)
            cloud_bottom = min(span_a, span_b)
            
            if signal.side == OrderSide.BUY and current_price < cloud_bottom:
                logger.debug(f"Skipping buy for {signal.symbol}: Price below Ichimoku Cloud")
                return False
            if signal.side == OrderSide.SELL and current_price > cloud_top:
                logger.debug(f"Skipping sell for {signal.symbol}: Price above Ichimoku Cloud")
                return False

        # Fibonacci Support/Resistance Zone check (Simplified)
        # Don't buy if price is just below a major Fib level (resistance)
        fib_618 = signal.indicators.get("fib_level_618")
        if fib_618 and signal.side == OrderSide.BUY:
            if current_price < fib_618 and (fib_618 - current_price) / current_price < 0.005:
                logger.debug(f"Skipping buy for {signal.symbol}: Approaching Fib 61.8% resistance")
                return False

        logger.info(f"Entry conditions met for {signal.symbol}")
        return True

    def should_exit(self, position: Position, current_price: float, data: pd.DataFrame) -> bool:
        """
        Determine if we should exit an open position.

        Args:
            position: Current position
            current_price: Current market price
            data: Recent market data

        Returns:
            True if should exit, False otherwise
        """
        # Check stop loss
        if self.use_stop_loss and position.stop_loss:
            if position.side == OrderSide.BUY and current_price <= position.stop_loss:
                logger.info(f"Stop loss hit for {position.symbol}: {current_price} <= {position.stop_loss}")
                return True
            elif position.side == OrderSide.SELL and current_price >= position.stop_loss:
                logger.info(f"Stop loss hit for {position.symbol}: {current_price} >= {position.stop_loss}")
                return True

        # Check take profit
        if self.use_take_profit and position.take_profit:
            if position.side == OrderSide.BUY and current_price >= position.take_profit:
                logger.info(f"Take profit hit for {position.symbol}: {current_price} >= {position.take_profit}")
                return True
            elif position.side == OrderSide.SELL and current_price <= position.take_profit:
                logger.info(f"Take profit hit for {position.symbol}: {current_price} <= {position.take_profit}")
                return True

        # Advanced Ichimoku Exit: Price crossing Kijun-sen
        if "kijun_sen" in data.columns:
            kijun = data["kijun_sen"].iloc[-1]
            if position.side == OrderSide.BUY and current_price < kijun:
                logger.info(f"Ichimoku Exit: {position.symbol} price broke below Kijun-sen")
                return True
            if position.side == OrderSide.SELL and current_price > kijun:
                logger.info(f"Ichimoku Exit: {position.symbol} price broke above Kijun-sen")
                return True

        # Fibonacci Profit Lock: If price is above Fib 78.6% and drops below it
        if "fib_level_786" in data.columns:
            fib_786 = data["fib_level_786"].iloc[-1]
            if position.side == OrderSide.BUY and position.highest_price > fib_786 and current_price < fib_786:
                logger.info(f"Fibonacci Exit: {position.symbol} failed to hold 78.6% level")
                return True

        # Check for reverse signal
        signal = self.analyze(data)
        if signal:
            # Exit long if we get a sell signal
            if position.side == OrderSide.BUY and signal.side == OrderSide.SELL and signal.strength > 0.3:
                logger.info(f"Reverse signal detected for {position.symbol}")
                return True
            # Exit short if we get a buy signal
            elif position.side == OrderSide.SELL and signal.side == OrderSide.BUY and signal.strength > 0.3:
                logger.info(f"Reverse signal detected for {position.symbol}")
                return True

        return False


class MACDCrossoverStrategy(BaseStrategy):
    """
    Simple MACD crossover strategy.

    Entry:
    - Buy when MACD crosses above signal line
    - Sell when MACD crosses below signal line

    Exit:
    - Opposite crossover
    - Stop loss/take profit
    """

    def __init__(self, name: str = "MACDCrossoverStrategy"):
        super().__init__(name)
        self.indicators = TechnicalIndicators()

    def analyze(self, data: pd.DataFrame) -> Optional[Signal]:
        """Analyze data for MACD crossover."""
        try:
            # Calculate MACD
            macd, signal_line, hist = self.indicators.calculate_macd(data)

            if len(hist) < 2:
                return None

            current_hist = hist.iloc[-1]
            prev_hist = hist.iloc[-2]
            current_price = data["close"].iloc[-1]

            # Bullish crossover: histogram crosses above zero
            if current_hist > 0 and prev_hist <= 0:
                return Signal(
                    symbol=data.get("symbol", "UNKNOWN"),
                    side=OrderSide.BUY,
                    strength=0.7,
                    indicators={
                        "macd": macd.iloc[-1],
                        "signal": signal_line.iloc[-1],
                        "histogram": current_hist,
                        "close": current_price
                    }
                )

            # Bearish crossover: histogram crosses below zero
            if current_hist < 0 and prev_hist >= 0:
                return Signal(
                    symbol=data.get("symbol", "UNKNOWN"),
                    side=OrderSide.SELL,
                    strength=0.7,
                    indicators={
                        "macd": macd.iloc[-1],
                        "signal": signal_line.iloc[-1],
                        "histogram": current_hist,
                        "close": current_price
                    }
                )

            return None

        except Exception as e:
            logger.error(f"Error in MACD analysis: {e}")
            return None

    def should_enter(self, signal: Signal, current_price: float, account_balance: float) -> bool:
        """Check if we should enter based on MACD signal."""
        # Simple entry: any signal with sufficient balance
        if account_balance < 100:
            return False

        # No conflicting positions
        if self.get_open_positions(signal.symbol):
            return False

        return True

    def should_exit(self, position: Position, current_price: float, data: pd.DataFrame) -> bool:
        """Exit on reverse crossover or stop loss."""
        # Check stop loss
        if position.stop_loss:
            if position.side == OrderSide.BUY and current_price <= position.stop_loss:
                return True
            if position.side == OrderSide.SELL and current_price >= position.stop_loss:
                return True

        # Check for reverse signal
        signal = self.analyze(data)
        if signal:
            if position.side == OrderSide.BUY and signal.side == OrderSide.SELL:
                return True
            if position.side == OrderSide.SELL and signal.side == OrderSide.BUY:
                return True

        return False
