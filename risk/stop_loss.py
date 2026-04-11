"""
Stop loss and take profit management.
Calculates and manages stop loss levels for positions.
"""

from typing import Optional, Tuple
from enum import Enum
import pandas as pd
from loguru import logger


class StopLossType(Enum):
    """Stop loss calculation methods."""
    FIXED_PERCENT = "fixed_percent"  # Fixed percentage from entry
    ATR = "atr"  # Based on Average True Range
    SUPPORT_RESISTANCE = "support_resistance"  # Based on S/R levels
    TRAILING = "trailing"  # Trailing stop loss
    VOLATILITY = "volatility"  # Based on volatility


class StopLossManager:
    """
    Calculate and manage stop loss levels.
    """

    def __init__(
        self,
        stop_loss_type: StopLossType = StopLossType.FIXED_PERCENT,
        stop_loss_percent: float = 0.05,  # 5% stop loss
        take_profit_percent: float = 0.10,  # 10% take profit
        trailing_percent: float = 0.03,  # 3% trailing stop
        atr_multiplier: float = 2.0  # 2x ATR for stop loss
    ):
        self.stop_loss_type = stop_loss_type
        self.stop_loss_percent = stop_loss_percent
        self.take_profit_percent = take_profit_percent
        self.trailing_percent = trailing_percent
        self.atr_multiplier = atr_multiplier
        logger.info(f"StopLossManager initialized: type={stop_loss_type.value}")

    def calculate_stop_loss(
        self,
        entry_price: float,
        is_long: bool,
        atr: Optional[float] = None,
        support_level: Optional[float] = None,
        resistance_level: Optional[float] = None
    ) -> float:
        """
        Calculate stop loss price.

        Args:
            entry_price: Entry price for the position
            is_long: True for long position, False for short
            atr: Average True Range (for ATR method)
            support_level: Support price level
            resistance_level: Resistance price level

        Returns:
            Stop loss price
        """
        if self.stop_loss_type == StopLossType.FIXED_PERCENT:
            stop_loss = self._fixed_percent_stop(entry_price, is_long)

        elif self.stop_loss_type == StopLossType.ATR:
            if not atr:
                logger.warning("ATR not provided, falling back to fixed percent")
                stop_loss = self._fixed_percent_stop(entry_price, is_long)
            else:
                stop_loss = self._atr_stop(entry_price, is_long, atr)

        elif self.stop_loss_type == StopLossType.SUPPORT_RESISTANCE:
            if is_long and not support_level:
                logger.warning("Support level not provided, falling back to fixed percent")
                stop_loss = self._fixed_percent_stop(entry_price, is_long)
            elif not is_long and not resistance_level:
                logger.warning("Resistance level not provided, falling back to fixed percent")
                stop_loss = self._fixed_percent_stop(entry_price, is_long)
            else:
                stop_loss = self._support_resistance_stop(
                    entry_price, is_long, support_level, resistance_level
                )

        elif self.stop_loss_type == StopLossType.TRAILING:
            # Trailing stop starts at fixed percent
            stop_loss = self._fixed_percent_stop(entry_price, is_long)

        else:
            logger.error(f"Unknown stop loss type: {self.stop_loss_type}")
            stop_loss = self._fixed_percent_stop(entry_price, is_long)

        logger.debug(f"Stop loss calculated: ${stop_loss:.2f} for entry ${entry_price:.2f}")
        return stop_loss

    def calculate_take_profit(self, entry_price: float, is_long: bool) -> float:
        """
        Calculate take profit price.

        Args:
            entry_price: Entry price for the position
            is_long: True for long position, False for short

        Returns:
            Take profit price
        """
        if is_long:
            take_profit = entry_price * (1 + self.take_profit_percent)
        else:
            take_profit = entry_price * (1 - self.take_profit_percent)

        logger.debug(f"Take profit calculated: ${take_profit:.2f} for entry ${entry_price:.2f}")
        return take_profit

    def calculate_both(
        self,
        entry_price: float,
        is_long: bool,
        atr: Optional[float] = None,
        support_level: Optional[float] = None,
        resistance_level: Optional[float] = None
    ) -> Tuple[float, float]:
        """
        Calculate both stop loss and take profit.

        Returns:
            Tuple of (stop_loss, take_profit)
        """
        stop_loss = self.calculate_stop_loss(
            entry_price, is_long, atr, support_level, resistance_level
        )
        take_profit = self.calculate_take_profit(entry_price, is_long)
        return stop_loss, take_profit

    def update_trailing_stop(
        self,
        current_stop: float,
        current_price: float,
        highest_price: float,
        is_long: bool
    ) -> float:
        """
        Update trailing stop loss.

        Args:
            current_stop: Current stop loss price
            current_price: Current market price
            highest_price: Highest price since entry (for long) or lowest for short
            is_long: True for long position

        Returns:
            Updated stop loss price
        """
        if is_long:
            # For long: trail up as price increases
            new_stop = highest_price * (1 - self.trailing_percent)
            # Only move stop loss up, never down
            return max(current_stop, new_stop)
        else:
            # For short: trail down as price decreases
            lowest_price = highest_price  # Parameter is misnamed for shorts
            new_stop = lowest_price * (1 + self.trailing_percent)
            # Only move stop loss down, never up
            return min(current_stop, new_stop)

    def _fixed_percent_stop(self, entry_price: float, is_long: bool) -> float:
        """Fixed percentage stop loss."""
        if is_long:
            return entry_price * (1 - self.stop_loss_percent)
        else:
            return entry_price * (1 + self.stop_loss_percent)

    def _atr_stop(self, entry_price: float, is_long: bool, atr: float) -> float:
        """ATR-based stop loss."""
        stop_distance = atr * self.atr_multiplier
        if is_long:
            return entry_price - stop_distance
        else:
            return entry_price + stop_distance

    def _support_resistance_stop(
        self,
        entry_price: float,
        is_long: bool,
        support_level: Optional[float],
        resistance_level: Optional[float]
    ) -> float:
        """Support/resistance-based stop loss."""
        if is_long:
            # Place stop below support
            stop = support_level * 0.995 if support_level else entry_price * 0.95
        else:
            # Place stop above resistance
            stop = resistance_level * 1.005 if resistance_level else entry_price * 1.05

        return stop

    def calculate_atr(self, data: pd.DataFrame, period: int = 14) -> float:
        """
        Calculate Average True Range.

        Args:
            data: DataFrame with high, low, close columns
            period: ATR period (default 14)

        Returns:
            ATR value
        """
        try:
            high = data["high"]
            low = data["low"]
            close = data["close"]

            # True Range calculation
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())

            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

            # ATR is the moving average of true range
            atr = true_range.rolling(window=period).mean().iloc[-1]

            logger.debug(f"ATR calculated: {atr:.2f}")
            return atr

        except Exception as e:
            logger.error(f"Error calculating ATR: {e}")
            return 0.0

    def calculate_risk_reward_ratio(
        self,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        is_long: bool
    ) -> float:
        """
        Calculate risk/reward ratio.

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            is_long: True for long position

        Returns:
            Risk/reward ratio (e.g., 2.0 means 2:1 reward:risk)
        """
        if is_long:
            risk = entry_price - stop_loss
            reward = take_profit - entry_price
        else:
            risk = stop_loss - entry_price
            reward = entry_price - take_profit

        if risk <= 0:
            logger.warning("Invalid risk calculation")
            return 0.0

        ratio = reward / risk
        logger.debug(f"Risk/Reward ratio: {ratio:.2f}:1")
        return ratio

    def validate_stop_loss(
        self,
        entry_price: float,
        stop_loss: float,
        is_long: bool,
        max_loss_percent: float = 0.20
    ) -> bool:
        """
        Validate if stop loss is reasonable.

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            is_long: True for long position
            max_loss_percent: Maximum acceptable loss percentage

        Returns:
            True if valid, False otherwise
        """
        if is_long:
            loss_percent = (entry_price - stop_loss) / entry_price
            if stop_loss >= entry_price:
                logger.error("Stop loss for long position must be below entry")
                return False
        else:
            loss_percent = (stop_loss - entry_price) / entry_price
            if stop_loss <= entry_price:
                logger.error("Stop loss for short position must be above entry")
                return False

        if loss_percent > max_loss_percent:
            logger.warning(f"Stop loss {loss_percent*100:.1f}% exceeds maximum {max_loss_percent*100:.1f}%")
            return False

        if loss_percent < 0.01:  # Less than 1%
            logger.warning(f"Stop loss {loss_percent*100:.1f}% too tight")
            return False

        return True


# Example usage
def main():
    manager = StopLossManager(
        stop_loss_type=StopLossType.FIXED_PERCENT,
        stop_loss_percent=0.05,
        take_profit_percent=0.10
    )

    entry_price = 100.0
    is_long = True

    # Calculate stop loss and take profit
    stop_loss, take_profit = manager.calculate_both(entry_price, is_long)

    print(f"Entry Price: ${entry_price:.2f}")
    print(f"Stop Loss: ${stop_loss:.2f} ({((entry_price - stop_loss) / entry_price * 100):.1f}% loss)")
    print(f"Take Profit: ${take_profit:.2f} ({((take_profit - entry_price) / entry_price * 100):.1f}% gain)")

    # Calculate risk/reward
    rr_ratio = manager.calculate_risk_reward_ratio(entry_price, stop_loss, take_profit, is_long)
    print(f"Risk/Reward Ratio: {rr_ratio:.2f}:1")

    # Validate
    is_valid = manager.validate_stop_loss(entry_price, stop_loss, is_long)
    print(f"Valid: {is_valid}")


if __name__ == "__main__":
    main()
