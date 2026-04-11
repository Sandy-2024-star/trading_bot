"""
Base SQLAlchemy configuration and engine setup.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from config.config import config
import os

# Create data directory if it doesn't exist (for SQLite fallback)
os.makedirs("data", exist_ok=True)

# Database URL from config (PostgreSQL or SQLite fallback)
if config.POSTGRES_PASSWORD:
    db_url = config.get_postgres_url()
else:
    # Default to SQLite for development if no Postgres credentials provided
    db_url = "sqlite:///data/trading_bot.db"

# Create engine
engine = create_engine(
    db_url,
    echo=False,
    pool_pre_ping=True
)

# Create session factory
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

# Base class for models
Base = declarative_base()

def init_db():
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(engine)
