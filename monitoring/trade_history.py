"""
Trade history monitoring and reporting.
Provides tools to query and display historical trades and orders.
"""

from typing import List, Optional
import pandas as pd
from loguru import logger
from execution.repositories.trade_repository import TradeRepository
from execution.repositories.order_repository import OrderRepository
from database import Session

class TradeHistoryManager:
    """Manages querying and reporting of trade and order history."""

    def __init__(self, trade_repo: TradeRepository, order_repo: OrderRepository):
        self.trade_repo = trade_repo
        self.order_repo = order_repo

    def get_trade_history_df(self, symbol: Optional[str] = None) -> pd.DataFrame:
        """Get all trades as a pandas DataFrame."""
        trades = self.trade_repo.get_all(symbol)
        if not trades:
            return pd.DataFrame()
            
        data = [
            {
                "Trade ID": t.trade_id,
                "Order ID": t.order_id,
                "Symbol": t.symbol,
                "Side": t.side.value,
                "Qty": t.quantity,
                "Price": t.price,
                "Fees": t.fees,
                "PnL": t.pnl,
                "Timestamp": t.timestamp
            } for t in trades
        ]
        return pd.DataFrame(data).sort_values("Timestamp", ascending=False)

    def get_order_history_df(self, symbol: Optional[str] = None) -> pd.DataFrame:
        """Get all orders as a pandas DataFrame."""
        # Note: Need a 'get_all' in OrderRepository or similar
        # For now, let's use the session directly since it's a monitoring tool
        session = self.order_repo.session
        from database.models import OrderModel
        
        query = session.query(OrderModel)
        if symbol:
            query = query.filter(OrderModel.symbol == symbol)
            
        orders = query.all()
        if not orders:
            return pd.DataFrame()
            
        data = [
            {
                "Order ID": o.order_id,
                "Symbol": o.symbol,
                "Side": o.side.value,
                "Type": o.order_type.value,
                "Qty": o.quantity,
                "Price": o.price,
                "Status": o.status.value,
                "Filled Qty": o.filled_quantity,
                "Avg Price": o.average_fill_price,
                "Created At": o.created_at
            } for o in orders
        ]
        return pd.DataFrame(data).sort_values("Created At", ascending=False)

    def print_trade_summary(self, symbol: Optional[str] = None):
        """Print a summary of historical trades to the console."""
        df = self.get_trade_history_df(symbol)
        if df.empty:
            print("\n--- No Trade History Found ---")
            return

        print("\n--- Trade History Summary ---")
        print(df.to_string(index=False))
        
        total_pnl = df["PnL"].sum()
        total_fees = df["Fees"].sum()
        win_rate = (df["PnL"] > 0).mean() * 100
        
        print(f"\nTotal Trades: {len(df)}")
        print(f"Total PnL: ${total_pnl:.2f}")
        print(f"Total Fees: ${total_fees:.2f}")
        print(f"Win Rate: {win_rate:.1f}%")

def show_history(symbol: Optional[str] = None):
    """Convenience function to display history."""
    session = Session()
    try:
        trade_repo = TradeRepository(session)
        order_repo = OrderRepository(session)
        manager = TradeHistoryManager(trade_repo, order_repo)
        
        manager.print_trade_summary(symbol)
    finally:
        session.close()

if __name__ == "__main__":
    show_history()
