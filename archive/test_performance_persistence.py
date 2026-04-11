"""
Test script for performance tracking persistence.
"""

import sys
import os
import time
from datetime import datetime

# Ensure trading_bot is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Session, init_db
from monitoring.pnl_tracker import PnLTracker
from monitoring.repositories.performance_repository import PerformanceRepository
from monitoring.historical_analysis import HistoricalPerformanceAnalyzer

def test_performance_persistence():
    """Simulate PnL tracking and verify database persistence."""
    print("Testing Performance Tracking Persistence...")
    
    # Initialize DB
    init_db()
    
    # Setup
    session = Session()
    repo = PerformanceRepository(session)
    tracker = PnLTracker(initial_balance=10000.0, performance_repository=repo)
    
    # 1. Record some snapshots
    print("\nRecording simulated snapshots...")
    
    # Snapshot 1: Start
    tracker.record_snapshot(10000.0, 0.0, 0.0, 0.0)
    
    # Snapshot 2: Gain
    tracker.record_snapshot(9000.0, 1500.0, 500.0, 0.0)
    
    # Snapshot 3: Realized Gain
    tracker.record_snapshot(10500.0, 0.0, 0.0, 500.0)
    
    # 2. Verify via analyzer
    print("\nVerifying via HistoricalPerformanceAnalyzer...")
    analyzer = HistoricalPerformanceAnalyzer(repo)
    analyzer.print_performance_summary()
    
    df = analyzer.get_equity_curve_df()
    print(f"\nSnapshots in DB: {len(df)}")
    
    if len(df) >= 3:
        print("\nSUCCESS: Performance Persistence Verified!")
    else:
        print("\nFAILURE: Persistent records not found as expected.")
        
    session.close()

if __name__ == "__main__":
    test_performance_persistence()
