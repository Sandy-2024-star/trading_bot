"""
Tools for analyzing historical performance from the database.
"""

from typing import List, Optional
import pandas as pd
from monitoring.repositories.performance_repository import PerformanceRepository
from database import Session

class HistoricalPerformanceAnalyzer:
    """Analyzes historical performance data stored in the database."""

    def __init__(self, performance_repo: PerformanceRepository):
        self.perf_repo = performance_repo

    def get_equity_curve_df(self, limit: int = 1000) -> pd.DataFrame:
        """Get historical equity curve as a DataFrame."""
        snapshots = self.perf_repo.get_history(limit)
        if not snapshots:
            return pd.DataFrame()
            
        data = [
            {
                "Timestamp": s.timestamp,
                "Equity": s.total_equity,
                "Total PnL": s.total_pnl,
                "Daily PnL": s.daily_pnl,
                "Drawdown %": s.drawdown_pct
            } for s in snapshots
        ]
        # Sort by timestamp ascending for plotting/analysis
        return pd.DataFrame(data).sort_values("Timestamp")

    def print_performance_summary(self):
        """Print a summary of historical performance metrics."""
        df = self.get_equity_curve_df()
        if df.empty:
            print("\n--- No Performance History Found ---")
            return

        print("\n--- Historical Performance Summary ---")
        latest = df.iloc[-1]
        first = df.iloc[0]
        
        total_return = latest["Equity"] - first["Equity"]
        return_pct = (total_return / first["Equity"] * 100) if first["Equity"] > 0 else 0
        
        print(f"Start Equity: ${first['Equity']:,.2f} ({first['Timestamp']})")
        print(f"End Equity:   ${latest['Equity']:,.2f} ({latest['Timestamp']})")
        print(f"Total Return: ${total_return:,.2f} ({return_pct:.2f}%)")
        print(f"Max Drawdown: {df['Drawdown %'].max():.2f}%")
        print(f"Record Count: {len(df)}")

def show_performance():
    """Convenience function to display performance history."""
    session = Session()
    try:
        repo = PerformanceRepository(session)
        analyzer = HistoricalPerformanceAnalyzer(repo)
        analyzer.print_performance_summary()
    finally:
        session.close()

if __name__ == "__main__":
    show_performance()
