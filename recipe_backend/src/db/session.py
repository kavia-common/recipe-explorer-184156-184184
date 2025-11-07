import os
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base

# SQLAlchemy Declarative Base used by models
Base = declarative_base()


def _resolve_database_url() -> str:
    """
    Resolve the database URL from environment variables with a safe fallback.
    Priority:
      1. DATABASE_URL (should be a SQLAlchemy URL; for Postgres use postgresql+psycopg2://)
      2. Fallback to local SQLite file for tests/local runs
    """
    url = os.getenv("DATABASE_URL")
    if url and url.strip():
        # Allow DATABASE_URL env to specify postgres or any supported DB
        # Normalize common postgres scheme if necessary.
        if url.startswith("postgres://"):
            # SQLAlchemy expects postgresql+psycopg2 or postgresql
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url
    # Default fallback for local/testing
    return "sqlite:///./test.db"


def _create_engine(db_url: str) -> Engine:
    """
    Create the SQLAlchemy engine with sensible defaults depending on the backend.
    - SQLite requires check_same_thread=False for typical FastAPI threaded usage.
    - For Postgres, use default engine creation.
    """
    connect_args = {}
    if db_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    engine = create_engine(db_url, echo=False, future=True, connect_args=connect_args)
    return engine


DATABASE_URL = _resolve_database_url()
engine: Engine = _create_engine(DATABASE_URL)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
    future=True,
)


# PUBLIC_INTERFACE
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session and ensures proper cleanup.

    Yields:
        sqlalchemy.orm.Session: An active SQLAlchemy Session bound to the configured engine.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """
    Context manager for non-FastAPI usage or scripts.

    Example:
        with db_session() as session:
            session.query(...)

    Yields:
        sqlalchemy.orm.Session: A session bound to the configured engine.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def run_create_all(models_base: Optional[declarative_base] = None) -> None:
    """
    Helper to create all tables using metadata. Intended for bootstrap/startup.
    """
    base_meta = (models_base or Base).metadata
    base_meta.create_all(bind=engine)
