"""
Database Configuration and Session Factory for Personalization Persistence.
"""

import os
from typing import Generator, Optional
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session

DEFAULT_DATABASE_URL = "postgresql://username:password@localhost:5432/emotion_visualization"


def get_database_url() -> Optional[str]:
    """
    Retrieve DATABASE_URL from the environment.
    Returns None if DATABASE_URL is not set.
    """
    return os.getenv("DATABASE_URL")


def create_db_engine(url: Optional[str] = None, **kwargs) -> Engine:
    """
    Instantiate an SQLAlchemy Engine.
    Uses modern Psycopg 3 (psycopg) driver with SQLAlchemy 2.x.
    """
    db_url = url or get_database_url() or DEFAULT_DATABASE_URL
    # Normalize postgres:// to postgresql:// if needed for SQLAlchemy 2.x
    if db_url.startswith("postgres://"):
        db_url = "postgresql://" + db_url[len("postgres://"):]
    return create_engine(db_url, **kwargs)


def get_session_factory(engine: Optional[Engine] = None) -> sessionmaker[Session]:
    """Return a configured sessionmaker bound to the given or default engine."""
    eng = engine or create_db_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=eng)
