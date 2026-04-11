"""
Repository for managing Position persistence.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from database.models import PositionModel
from core.base_strategy import Position, OrderSide

class PositionRepository:
    """Handles database operations for Position entities."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, position: Position) -> PositionModel:
        """Save or update a position in the database."""
        db_position = self.session.query(PositionModel).filter_by(symbol=position.symbol, is_open=True).first()
        
        if not db_position:
            db_position = PositionModel(
                symbol=position.symbol,
                side=position.side,
                size=position.size,
                entry_price=position.entry_price,
                stop_loss=position.stop_loss,
                take_profit=position.take_profit,
                timestamp=position.timestamp,
                is_open=position.is_open,
                highest_price=getattr(position, 'highest_price', position.entry_price)
            )
            self.session.add(db_position)
        else:
            # Update mutable fields
            db_position.stop_loss = position.stop_loss
            db_position.take_profit = position.take_profit
            db_position.exit_price = position.exit_price
            db_position.exit_timestamp = position.exit_timestamp
            db_position.is_open = position.is_open
            db_position.highest_price = getattr(position, 'highest_price', db_position.highest_price)

        self.session.commit()
        return db_position

    def get_open_positions(self) -> List[Position]:
        """Retrieve all open positions."""
        db_positions = self.session.query(PositionModel).filter_by(is_open=True).all()
        return [
            self._to_strategy_position(db) for db in db_positions
        ]

    def _to_strategy_position(self, db: PositionModel) -> Position:
        """Convert database model to strategy position object."""
        pos = Position(
            symbol=db.symbol,
            side=db.side,
            size=db.size,
            entry_price=db.entry_price,
            stop_loss=db.stop_loss,
            take_profit=db.take_profit,
            timestamp=db.timestamp
        )
        pos.is_open = db.is_open
        pos.exit_price = db.exit_price
        pos.exit_timestamp = db.exit_timestamp
        # Add highest_price attribute dynamically if not in base class yet
        pos.highest_price = db.highest_price
        return pos
