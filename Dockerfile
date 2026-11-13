FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Install dependencies first so the layer caches independently of app code.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

# Non-root user; /data holds the SQLite database (mounted as a volume).
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /data \
    && chown appuser:appuser /data /app
USER appuser

ENV UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BASE_URL=http://localhost:8000 \
    DATABASE_URL=sqlite+aiosqlite:////data/industry.db

EXPOSE 8000

# Migrations run before the server on every start; alembic upgrade is a
# no-op when the schema is current.
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"]
