"""Database engine, session factory, and shared declarative base."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime

from sqlalchemy import DateTime
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


def make_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(database_url, echo=False)


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
