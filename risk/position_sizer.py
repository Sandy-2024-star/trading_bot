"""
Position sizing calculator.
Determines optimal position size based on risk management rules.
"""

from typing import Dict, Optional
from enum import Enum
from loguru import logger


class SizingMethod(Enum):
    """Position sizing methods."""
    FIXED = "fixed"  # Fixed dollar amount
    PERCENT_EQUITY = "percent_equity"  # Percentage of account equity
    RISK_BASED = "risk_based"  # Based on risk per trade
    KELLY = "kelly"  # Kelly criterion
    VOLATILITY = "volatility"  # Based on ATR/volatility


class PositionSizer:
    """
    Calculate position sizes based on various methods.
    """

    def __init__(
        self,
        method: SizingMethod = SizingMethod.RISK_BASED,
        risk_per_trade: float = 0.02,  # 2% risk per trade
        max_position_size: float = 10000,  # Max $10k per position
        min_position_size: float = 100,  # Min $100 per position
        max_portfolio_heat: float = 0.06  # Max 6% total risk across all positions
    ):
        self.method = method
        self.risk_per_trade = risk_per_trade
        self.max_position_size = max_position_size
        self.min_position_size = min_position_size
        self.max_portfolio_heat = max_portfolio_heat
        logger.info(f"PositionSizer initialized: method={method.value}, risk={risk_per_trade*100}%, max_heat={max_portfolio_heat*100}%")

    def calculate_risk_amount(self, entry_price: float, stop_loss_price: float, quantity: float) -> float:
        """Calculate the dollar amount at risk for a position."""
        return abs(entry_price - stop_loss_price) * quantity

    def validate_portfolio_heat(self, current_risk_amount: float, new_trade_risk_amount: float, account_balance: float) -> bool:
        """
        Check if adding a new trade exceeds the maximum portfolio heat.
        
        Args:
            current_risk_amount: Total $ risk of all currently open positions
            new_trade_risk_amount: $ risk of the proposed new trade
            account_balance: Current account balance
            
        Returns:
            True if within limits, False otherwise
        """
        total_risk = current_risk_amount + new_trade_risk_amount
        heat = total_risk / account_balance if account_balance > 0 else 1.0
        
        if heat > self.max_portfolio_heat:
            logger.warning(f"Portfolio heat {heat*100:.1f}% exceeds maximum {self.max_portfolio_heat*100:.1f}%")
            return False
            
        return True

    def calculate_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss_price: Optional[float] = None,
        signal_strength: float = 1.0
    ) -> float:
        """
        Calculate position size based on selected method.

        Args:
            account_balance: Current account balance
            entry_price: Planned entry price
            stop_loss_price: Stop loss price (required for risk-based)
            signal_strength: Signal strength (0-1) for position scaling

        Returns:
            Position size in base currency units
        """
        if self.method == SizingMethod.FIXED:
            size = self._fixed_size(account_balance)

        elif self.method == SizingMethod.PERCENT_EQUITY:
            size = self._percent_equity_size(account_balance, entry_price)

        elif self.method == SizingMethod.RISK_BASED:
            if not stop_loss_price:
                logger.warning("Stop loss price required for risk-based sizing, falling back to percent equity")
                size = self._percent_equity_size(account_balance, entry_price)
            else:
                size = self._risk_based_size(account_balance, entry_price, stop_loss_price)

        elif self.method == SizingMethod.KELLY:
            size = self._kelly_size(account_balance, entry_price)

        elif self.method == SizingMethod.VOLATILITY:
            size = self._volatility_size(account_balance, entry_price)

        else:
            logger.error(f"Unknown sizing method: {self.method}")
            size = self.min_position_size

        # Scale by signal strength
        size = size * signal_strength

        # Apply min/max constraints
        size = max(self.min_position_size, min(size, self.max_position_size))

        logger.debug(f"Calculated position size: ${size:.2f} ({self.method.value})")
        return size

    def _fixed_size(self, account_balance: float) -> float:
        """Fixed dollar amount sizing."""
        return min(self.max_position_size, account_balance * 0.1)

    def _percent_equity_size(self, account_balance: float, entry_price: float) -> float:
        """
        Percentage of equity sizing.
        Allocate a fixed percentage of account to the position.
        """
        position_value = account_balance * self.risk_per_trade * 10  # 2% risk -> 20% allocation
        return position_value

    def _risk_based_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss_price: float
    ) -> float:
        """
        Risk-based position sizing.
        Position size = (Account Risk) / (Per Unit Risk)

        Example:
        - Account: $10,000
        - Risk per trade: 2% = $200
        - Entry: $100
        - Stop loss: $95
        - Per unit risk: $100 - $95 = $5
        - Position size: $200 / $5 = 40 units -> $4,000 position
        """
        risk_amount = account_balance * self.risk_per_trade
        per_unit_risk = abs(entry_price - stop_loss_price)

        if per_unit_risk == 0:
            logger.warning("Per unit risk is zero, using percent equity sizing")
            return self._percent_equity_size(account_balance, entry_price)

        # Calculate number of units
        units = risk_amount / per_unit_risk

        # Position value
        position_value = units * entry_price

        logger.debug(
            f"Risk-based sizing: risk=${risk_amount:.2f}, "
            f"per_unit_risk=${per_unit_risk:.2f}, units={units:.2f}, "
            f"position=${position_value:.2f}"
        )

        return position_value

    def _kelly_size(self, account_balance: float, entry_price: float) -> float:
        """
        Kelly criterion sizing.
        Kelly % = W - [(1 - W) / R]
        Where W = win rate, R = average win/loss ratio

        For simplicity, using a conservative fixed Kelly fraction.
        """
        kelly_fraction = 0.25  # Conservative 25% of Kelly
        position_value = account_balance * kelly_fraction
        return position_value

    def _volatility_size(self, account_balance: float, entry_price: float) -> float:
        """
        Volatility-based sizing.
        Adjust position size inversely to volatility.
        Higher volatility = smaller position.

        This is a simplified version; real implementation would use ATR.
        """
        # Placeholder: use percent equity with volatility adjustment
        base_size = account_balance * self.risk_per_trade * 5
        volatility_adjustment = 1.0  # Would be calculated from ATR in real implementation
        return base_size / volatility_adjustment

    def calculate_quantity(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss_price: Optional[float] = None,
        signal_strength: float = 1.0
    ) -> float:
        """
        Calculate position quantity (number of units).

        Args:
            account_balance: Current account balance
            entry_price: Planned entry price
            stop_loss_price: Stop loss price
            signal_strength: Signal strength (0-1)

        Returns:
            Number of units to trade
        """
        position_value = self.calculate_size(
            account_balance,
            entry_price,
            stop_loss_price,
            signal_strength
        )

        quantity = position_value / entry_price
        return quantity

    def validate_size(self, size: float, account_balance: float) -> bool:
        """
        Validate if the position size is within acceptable limits.

        Args:
            size: Position size in dollars
            account_balance: Current account balance

        Returns:
            True if valid, False otherwise
        """
        # Check minimum size
        if size < self.min_position_size:
            logger.warning(f"Position size ${size:.2f} below minimum ${self.min_position_size}")
            return False

        # Check maximum size
        if size > self.max_position_size:
            logger.warning(f"Position size ${size:.2f} above maximum ${self.max_position_size}")
            return False

        # Check if we have sufficient balance
        if size > account_balance:
            logger.warning(f"Position size ${size:.2f} exceeds account balance ${account_balance:.2f}")
            return False

        # Check if position is too large relative to account
        if size > account_balance * 0.5:  # Max 50% of account per position
            logger.warning(f"Position size ${size:.2f} exceeds 50% of account")
            return False

        return True


# Example usage
def main():
    sizer = PositionSizer(
        method=SizingMethod.RISK_BASED,
        risk_per_trade=0.02,
        max_position_size=10000,
        min_position_size=100
    )

    account_balance = 10000
    entry_price = 100
    stop_loss = 95

    # Calculate position size
    size = sizer.calculate_size(account_balance, entry_price, stop_loss)
    quantity = sizer.calculate_quantity(account_balance, entry_price, stop_loss)

    print(f"Account: ${account_balance:,.2f}")
    print(f"Entry: ${entry_price:.2f}")
    print(f"Stop Loss: ${stop_loss:.2f}")
    print(f"Position Size: ${size:,.2f}")
    print(f"Quantity: {quantity:.4f} units")
    print(f"Valid: {sizer.validate_size(size, account_balance)}")


if __name__ == "__main__":
    main()
