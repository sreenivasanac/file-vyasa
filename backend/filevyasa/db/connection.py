"""Database connection and session management."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from filevyasa.config import get_db_path
from filevyasa.db.tables import Base

# Global engine and session maker
_engine = None
_async_engine = None
_session_maker = None
_async_session_maker = None


def get_db_url() -> str:
    """Get the SQLite database URL."""
    db_path = get_db_path()
    return f"sqlite:///{db_path}"


def get_async_db_url() -> str:
    """Get the async SQLite database URL."""
    db_path = get_db_path()
    return f"sqlite+aiosqlite:///{db_path}"


def init_db() -> None:
    """Initialize the database and create tables."""
    global _engine, _session_maker

    db_url = get_db_url()
    _engine = create_engine(
        db_url, echo=False, connect_args={"check_same_thread": False}
    )
    _session_maker = sessionmaker(bind=_engine)

    # Create all tables
    Base.metadata.create_all(_engine)
    _ensure_new_columns(_engine)


async def init_async_db() -> None:
    """Initialize the async database and create tables."""
    global _async_engine, _async_session_maker

    db_url = get_async_db_url()
    _async_engine = create_async_engine(db_url, echo=False)
    _async_session_maker = async_sessionmaker(_async_engine, expire_on_commit=False)

    # Create all tables
    async with _async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_ensure_new_columns)


def get_db():
    """Get a synchronous database session."""
    if _session_maker is None:
        init_db()
    return _session_maker()


def get_session() -> Session:
    """Get a synchronous database session (alias for get_db)."""
    return get_db()


def _ensure_new_columns(engine):
    """Best-effort migration to add newly introduced columns for existing databases."""
    inspector = inspect(engine)
    expected = {
        "monitored_folders": [
            ("last_sync_started_at", "DATETIME"),
            ("skipped_files", "INTEGER DEFAULT 0"),
            ("excluded_paths", "JSON DEFAULT '[]'"),
        ],
        "file_objects": [
            ("last_extracted_at", "DATETIME"),
            ("last_ai_processed_at", "DATETIME"),
        ],
    }

    with engine.begin() as conn:
        for table, cols in expected.items():
            existing = {col['name'] for col in inspector.get_columns(table)}
            for name, ddl_type in cols:
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl_type}"))


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session."""
    if _async_session_maker is None:
        await init_async_db()

    async with _async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
