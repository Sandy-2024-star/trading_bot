"""
Script to test database persistence by saving and retrieving sample records.
"""

import sys
import os
from datetime import datetime

# Ensure trading_bot is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Session, init_db, OrderModel, TradeModel
from core.base_broker import OrderStatus, OrderSide, OrderType

def test_persistence():
    """Test saving and retrieving data."""
    print("Testing data persistence...")
    
    # Initialize DB (create tables)
    init_db()
    
    session = Session()
    try:
        # Create a sample order
        order_id = f"test_order_{int(datetime.now().timestamp())}"
        order = OrderModel(
            order_id=order_id,
            symbol="BTCUSD",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=0.1,
            status=OrderStatus.FILLED,
            filled_quantity=0.1,
            average_fill_price=50000.0,
            created_at=datetime.now(),
            filled_at=datetime.now(),
            notes="Persistence test order"
        )
        session.add(order)
        session.commit()
        print(f"Sample order {order_id} saved.")
        
        # Create a sample trade linked to the order
        trade_id = f"test_trade_{int(datetime.now().timestamp())}"
        trade = TradeModel(
            trade_id=trade_id,
            order_id=order_id,
            symbol="BTCUSD",
            side=OrderSide.BUY,
            quantity=0.1,
            price=50000.0,
            timestamp=datetime.now(),
            pnl=0.0
        )
        session.add(trade)
        session.commit()
        print(f"Sample trade {trade_id} saved.")
        
        # Retrieve from DB
        retrieved_order = session.query(OrderModel).filter_by(order_id=order_id).first()
        print(f"Retrieved order: {retrieved_order.order_id}, status={retrieved_order.status.value}")
        
        retrieved_trade = session.query(TradeModel).filter_by(trade_id=trade_id).first()
        print(f"Retrieved trade: {retrieved_trade.trade_id}, linked to order: {retrieved_trade.order.order_id}")
        
        if retrieved_order and retrieved_trade and retrieved_trade.order_id == order_id:
            print("Persistence test PASSED!")
        else:
            print("Persistence test FAILED!")
            
    except Exception as e:
        session.rollback()
        print(f"Error during persistence test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_persistence()
