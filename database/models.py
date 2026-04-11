"""
SQLAlchemy models for the trading bot.
Defines tables for orders, trades, positions, and sentiment data.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database.base import Base
from core.base_broker import OrderStatus, OrderSide, OrderType


class OrderModel(Base):
    """Database model for trading orders."""
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(String(50), unique=True, index=True)
    symbol = Column(String(20), index=True)
    side = Column(Enum(OrderSide))
    order_type = Column(Enum(OrderType))
    quantity = Column(Float)
    price = Column(Float, nullable=True)
    stop_price = Column(Float, nullable=True)
    status = Column(Enum(OrderStatus))
    filled_quantity = Column(Float, default=0.0)
    average_fill_price = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.now)
    filled_at = Column(DateTime, nullable=True)
    fees = Column(Float, default=0.0)
    notes = Column(String(255), nullable=True)
    
    # Relationship to trades
    trades = relationship("TradeModel", back_populates="order")


class TradeModel(Base):
    """Database model for executed trades."""
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    trade_id = Column(String(50), unique=True, index=True)
    order_id = Column(String(50), ForeignKey('orders.order_id'), index=True)
    symbol = Column(String(20), index=True)
    side = Column(Enum(OrderSide))
    quantity = Column(Float)
    price = Column(Float)
    fees = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.now)
    pnl = Column(Float, default=0.0)
    
    # Relationship to order
    order = relationship("OrderModel", back_populates="trades")


class PositionModel(Base):
    """Database model for open/closed positions."""
    __tablename__ = 'positions'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), unique=True, index=True)
    side = Column(Enum(OrderSide))
    size = Column(Float)
    entry_price = Column(Float)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.now)
    exit_price = Column(Float, nullable=True)
    exit_timestamp = Column(DateTime, nullable=True)
    highest_price = Column(Float, nullable=True)
    is_open = Column(Boolean, default=True)


class SentimentSnapshotModel(Base):
    """Database model for market sentiment data."""
    __tablename__ = 'sentiment_snapshots'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), index=True)
    score = Column(Float)
    label = Column(String(20))
    article_count = Column(Integer)
    timestamp = Column(DateTime, default=datetime.now)
    provider = Column(String(50))


class PerformanceSnapshotModel(Base):
    """Database model for account performance snapshots."""
    __tablename__ = 'performance_snapshots'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    total_equity = Column(Float)
    daily_pnl = Column(Float)
    total_pnl = Column(Float)
    drawdown_pct = Column(Float)
