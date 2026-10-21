"""
Database Configuration and Session Factory for Personalization Persistence.
"""

import os
from pathlib import Path
from typing import Generator, Optional
from dotenv import load_dotenv
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session

DEFAULT_DATABASE_URL = "postgresql://username:password@localhost:5432/emotion_visualization"

# Project root derived from this file's location: components/personalization/persistence/database.py -> parents[3]
PROJECT_ROOT = Path(__file__).resolve().parents[3]


def load_project_env(env_path: Optional[Path] = None, override: bool = False) -> bool:
    """
    Load project-root .env file if present, preserving shell environment overrides.
    """
    target = env_path if env_path is not None else (PROJECT_ROOT / ".env")
    if target.is_file():
        return load_dotenv(dotenv_path=target, override=override)
    return False


# Automatically load on module import so DATABASE_URL is available for runtime and Alembic
load_project_env()


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
