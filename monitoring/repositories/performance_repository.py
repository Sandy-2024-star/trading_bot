"""
Repository for managing Performance persistence.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from database.models import PerformanceSnapshotModel

class PerformanceRepository:
    """Handles database operations for Performance snapshots."""

    def __init__(self, session: Session):
        self.session = session

    def save_snapshot(
        self, 
        total_equity: float, 
        total_pnl: float, 
        daily_pnl: float = 0.0,
        drawdown_pct: float = 0.0
    ) -> PerformanceSnapshotModel:
        """Save a new performance snapshot to the database."""
        snapshot = PerformanceSnapshotModel(
            total_equity=total_equity,
            total_pnl=total_pnl,
            daily_pnl=daily_pnl,
            drawdown_pct=drawdown_pct
        )
        self.session.add(snapshot)
        self.session.commit()
        return snapshot

    def get_history(self, limit: int = 100) -> List[PerformanceSnapshotModel]:
        """Retrieve recent performance history."""
        return self.session.query(PerformanceSnapshotModel)\
            .order_by(PerformanceSnapshotModel.timestamp.desc())\
            .limit(limit)\
            .all()

    def get_latest(self) -> Optional[PerformanceSnapshotModel]:
        """Get the most recent performance snapshot."""
        return self.session.query(PerformanceSnapshotModel)\
            .order_by(PerformanceSnapshotModel.timestamp.desc())\
            .first()
