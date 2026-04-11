# Database Migration & Initialization Guide

## 1. Initial Setup

The trading bot uses SQLAlchemy for database abstraction. By default, it uses a local SQLite database stored at `data/trading_bot.db`.

To initialize the database schema for the first time:

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/trading_bot
python3 -c "from database import init_db; init_db(); print('Database initialized!')"
```

## 2. Migrating to PostgreSQL (Production)

To switch from SQLite to PostgreSQL:

1.  **Install PostgreSQL**: Ensure you have a PostgreSQL server running.
2.  **Install psycopg2**: `pip install psycopg2-binary` (already in requirements.txt).
3.  **Update `.env`**:
    *   Set `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`.
    *   **Crucial**: Set `POSTGRES_PASSWORD`. If this is set, the bot will automatically switch to PostgreSQL.
4.  **Re-initialize**: Run the initialization command above to create the tables in the new Postgres database.

## 3. Handling Schema Changes (Alembic)

For complex projects, we recommend using **Alembic** for migrations.

### Initializing Alembic:
```bash
pip install alembic
alembic init alembic
```

### Creating a migration:
```bash
alembic revision --autogenerate -m "Initial schema"
```

### Applying migrations:
```bash
alembic upgrade head
```

---
*Note: Current models are stored in `trading_bot/database/models.py`.*
