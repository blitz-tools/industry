"""Database engine, session factory, and shared declarative base."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime

from sqlalchemy import DateTime, event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Naive UTC everywhere: timezone-aware datetimes are unreliable on SQLite.
# All expiry math goes through utc_now() so nothing else constructs datetimes.


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(), default=utc_now, onupdate=utc_now, nullable=False
    )


def make_engine(database_url: str, **engine_kwargs) -> AsyncEngine:
    """The one engine factory (the app and the test fixtures share it,
    so behavior like the SQLite pragma below can never drift between
    them). Extra kwargs pass straight through to create_async_engine."""
    engine = create_async_engine(database_url, echo=False, **engine_kwargs)
    if database_url.startswith("sqlite"):
        # SQLite does not enforce foreign keys unless told to — without
        # this, every ON DELETE rule in the models (the plan snapshots'
        # CASCADE, the superseded-by pointer's SET NULL) is dead DDL and
        # deleting a parent row orphans its children.
        @event.listens_for(engine.sync_engine, "connect")
        def _enforce_foreign_keys(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    return engine


def make_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def session_dependency(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Yield a DB session, rolling back on error."""
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
