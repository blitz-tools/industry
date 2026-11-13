"""Application factory."""

import asyncio
import contextlib
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .config import Settings, get_settings
from .db import make_engine, make_session_factory
from .esi.assets import asset_sync_loop
from .routes import assets, auth, web

_package_dir = Path(__file__).parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = app.state.settings
    app.state.http = httpx.AsyncClient(timeout=10.0)
    engine = make_engine(settings.database_url)
    app.state.session_factory = make_session_factory(engine)
    # Background asset sync (single-process, like the refresh locks in
    # esi/client.py): one tick shortly after startup, then per interval.
    sync_task = asyncio.create_task(
        asset_sync_loop(app.state.session_factory, app.state.http, settings)
    )
    yield
    sync_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await sync_task
    # Disposing the engine is critical under --reload, otherwise SQLite
    # connections outlive their event loop.
    await app.state.http.aclose()
    await engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="industry", lifespan=lifespan)
    app.state.settings = settings

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        same_site="lax",
        # Only mark the session cookie secure when actually served over TLS.
        https_only=settings.base_url.startswith("https://"),
    )

    app.include_router(auth.router)
    app.include_router(web.router)
    app.include_router(assets.router)
    app.mount("/static", StaticFiles(directory=_package_dir / "static"), name="static")
    return app


app = create_app()
