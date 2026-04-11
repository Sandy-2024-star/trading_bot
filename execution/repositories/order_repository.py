"""
Repository for managing Order persistence.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import OrderModel
from core.base_broker import Order, OrderStatus, OrderSide, OrderType

class OrderRepository:
    """Handles database operations for Order entities."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, order: Order) -> OrderModel:
        """Save or update an order in the database."""
        db_order = self.session.query(OrderModel).filter_by(order_id=order.order_id).first()
        
        if not db_order:
            db_order = OrderModel(
                order_id=order.order_id,
                symbol=order.symbol,
                side=order.side,
                order_type=order.order_type,
                quantity=order.quantity,
                price=order.price,
                stop_price=order.stop_price,
                status=order.status,
                created_at=order.created_at,
                notes=order.notes
            )
            self.session.add(db_order)
        else:
            # Update mutable fields
            db_order.status = order.status
            db_order.filled_quantity = order.filled_quantity
            db_order.average_fill_price = order.average_fill_price
            db_order.filled_at = order.filled_at
            db_order.fees = order.fees
            db_order.notes = order.notes

        self.session.commit()
        return db_order

    def get_by_id(self, order_id: str) -> Optional[Order]:
        """Retrieve an order by its unique ID."""
        db_order = self.session.query(OrderModel).filter_by(order_id=order_id).first()
        if not db_order:
            return None
            
        return Order(
            order_id=db_order.order_id,
            symbol=db_order.symbol,
            side=db_order.side,
            order_type=db_order.order_type,
            quantity=db_order.quantity,
            price=db_order.price,
            stop_price=db_order.stop_price,
            status=db_order.status,
            filled_quantity=db_order.filled_quantity,
            average_fill_price=db_order.average_fill_price,
            created_at=db_order.created_at,
            filled_at=db_order.filled_at,
            fees=db_order.fees,
            notes=db_order.notes
        )

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Retrieve all orders with an active status."""
        query = self.session.query(OrderModel).filter(
            OrderModel.status.in_([OrderStatus.PENDING, OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED])
        )
        if symbol:
            query = query.filter(OrderModel.symbol == symbol)
            
        db_orders = query.all()
        return [
            Order(
                order_id=db.order_id,
                symbol=db.symbol,
                side=db.side,
                order_type=db.order_type,
                quantity=db.quantity,
                price=db.price,
                stop_price=db.stop_price,
                status=db.status,
                filled_quantity=db.filled_quantity,
                average_fill_price=db.average_fill_price,
                created_at=db.created_at,
                filled_at=db.filled_at,
                fees=db.fees,
                notes=db.notes
            ) for db in db_orders
        ]
