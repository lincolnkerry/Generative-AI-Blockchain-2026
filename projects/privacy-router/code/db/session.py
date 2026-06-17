"""Database session management — SQLite for dev, PostgreSQL for production."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine

# Save env vars before load_dotenv (env takes precedence)
_env_db_url = os.environ.get("DATABASE_URL")

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DATABASE_URL = _env_db_url or os.getenv("DATABASE_URL", "sqlite:///privacy_router.db")

engine = create_engine(DATABASE_URL, echo=False)


def _migrate_db():
    """Run lightweight migrations for schema changes."""
    import sqlalchemy

    with engine.connect() as conn:
        # Check if is_essential column exists in masking_records
        try:
            result = conn.execute(sqlalchemy.text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='masking_records' AND column_name='is_essential'"
            ))
            if not result.fetchone():
                conn.execute(sqlalchemy.text(
                    "ALTER TABLE masking_records ADD COLUMN is_essential BOOLEAN NOT NULL DEFAULT false"
                ))
                conn.commit()
        except Exception:
            # SQLite or table doesn't exist yet — create_all will handle it
            pass


def init_db():
    """Create all tables and run migrations."""
    # Import all models so SQLModel.metadata knows about them
    import db.models  # noqa: F401
    SQLModel.metadata.create_all(engine)
    _migrate_db()


def get_session() -> Session:
    """Get a new database session."""
    return Session(engine)
