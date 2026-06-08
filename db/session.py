"""Database session management — SQLite for dev, PostgreSQL for production."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://privacy_router:privacy_router@localhost:5433/privacy_router")

engine = create_engine(DATABASE_URL, echo=False)


def init_db():
    """Create all tables."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """Get a new database session."""
    return Session(engine)
