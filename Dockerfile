# Shared base: dependency install only, cached independently of app code.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS base

WORKDIR /app

# Install dependencies first so the layer caches independently of app code.
COPY pyproject.toml uv.lock ./

# --- Development image -----------------------------------------------------
# Full dependency set including the dev group. Source code is NOT baked in:
# compose.dev.yml bind-mounts the repo at /app so edits and --reload work
# without rebuilds.
FROM base AS dev

# Keep the venv outside /app so the bind-mounted source cannot shadow it.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1
RUN uv sync --frozen

# No USER switch: under rootless podman, container root maps to the invoking
# user, so files written into the mount (caches, the dev DB) keep host
# ownership. pytest/ruff/alembic/uvicorn are on PATH directly.
CMD ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]

# --- Production image (default target) --------------------------------------
FROM base AS production

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
