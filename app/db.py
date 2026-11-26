"""Database engine, session factory, and shared declarative base."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import DateTime, event, func, select
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


async def sqlite_stats(db: AsyncSession, database_url: str) -> dict:
    """Read-time SQLite health facts for the Observability page (M15):
    storage usage (page stats plus the on-disk files, WAL included) and
    per-table row counts. Read-only — renders stay side-effect-free.
    File sizes are None on a non-file database (the test suite's
    in-memory engine); page stats and counts always read.

    Best-practice context for the numbers (recorded in TODO.md's
    observability item): freelist pages are reclaimable space (a large
    fraction = a VACUUM candidate), a persistent -wal file means
    journal_mode=WAL with un-checkpointed frames, and query response
    times are the missing headroom signal — future work on the engine's
    event hooks, not readable here."""
    conn = await db.connection()

    async def pragma(name: str) -> int | str:
        return (await conn.exec_driver_sql(f"PRAGMA {name}")).scalar()

    page_size = await pragma("page_size")
    page_count = await pragma("page_count")
    freelist_count = await pragma("freelist_count")
    journal_mode = await pragma("journal_mode")
    used_bytes = page_size * page_count
    free_bytes = page_size * freelist_count

    file_bytes: int | None = None
    wal_bytes: int | None = None
    prefix = "sqlite+aiosqlite://"
    if database_url.startswith(prefix):
        rest = database_url[len(prefix) :].strip("/")
        if rest:  # a file-backed database; empty means :memory:
            path = Path(rest[1:]) if rest.startswith("/") else Path(rest)
            if path.exists():
                file_bytes = path.stat().st_size
                wal = path.with_name(path.name + "-wal")
                wal_bytes = wal.stat().st_size if wal.exists() else 0

    tables = []
    total_rows = 0
    for table in Base.metadata.sorted_tables:
        count = (
            await db.execute(select(func.count()).select_from(table))
        ).scalar_one()
        tables.append({"name": table.name, "rows": count})
        total_rows += count
    tables.sort(key=lambda table: (-table["rows"], table["name"]))
    return {
        "used_bytes": used_bytes,
        "free_bytes": free_bytes,
        "file_bytes": file_bytes,
        "wal_bytes": wal_bytes,
        "journal_mode": journal_mode,
        "total_rows": total_rows,
        "tables": tables,
    }
