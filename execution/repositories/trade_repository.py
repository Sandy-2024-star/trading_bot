"""
Repository for managing Trade persistence.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from database.models import TradeModel
from core.base_broker import Trade, OrderSide

class TradeRepository:
    """Handles database operations for Trade entities."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, trade: Trade) -> TradeModel:
        """Save a new trade record into the database."""
        db_trade = self.session.query(TradeModel).filter_by(trade_id=trade.trade_id).first()
        
        if not db_trade:
            db_trade = TradeModel(
                trade_id=trade.trade_id,
                order_id=trade.order_id,
                symbol=trade.symbol,
                side=trade.side,
                quantity=trade.quantity,
                price=trade.price,
                fees=trade.fees,
                timestamp=trade.timestamp,
                pnl=trade.pnl
            )
            self.session.add(db_trade)
            self.session.commit()
            
        return db_trade

    def get_by_order_id(self, order_id: str) -> List[Trade]:
        """Retrieve all trades associated with a specific order."""
        db_trades = self.session.query(TradeModel).filter_by(order_id=order_id).all()
        return [
            Trade(
                trade_id=db.trade_id,
                order_id=db.order_id,
                symbol=db.symbol,
                side=db.side,
                quantity=db.quantity,
                price=db.price,
                fees=db.fees,
                timestamp=db.timestamp,
                pnl=db.pnl
            ) for db in db_trades
        ]

    def get_all(self, symbol: Optional[str] = None) -> List[Trade]:
        """Retrieve all historical trades, optionally filtered by symbol."""
        query = self.session.query(TradeModel)
        if symbol:
            query = query.filter(TradeModel.symbol == symbol)
            
        db_trades = query.all()
        return [
            Trade(
                trade_id=db.trade_id,
                order_id=db.order_id,
                symbol=db.symbol,
                side=db.side,
                quantity=db.quantity,
                price=db.price,
                fees=db.fees,
                timestamp=db.timestamp,
                pnl=db.pnl
            ) for db in db_trades
        ]
