"""Application factory."""

import asyncio
import contextlib
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .config import Settings, get_settings
from .db import make_engine, make_session_factory
from .esi.assets import asset_sync_loop
from .routes import admin, assets, auth, character, corp, structures, web
from .sde import sde_check_loop
from .templates import dev_site_version

_package_dir = Path(__file__).parent

# While this marker exists, the dev version endpoint tells browsers to hold
# their reloads — mid-development reloads are disruptive to anyone watching.
# Pause: touch the file; resume: remove it (the next poll reloads).
DEV_PAUSE_MARKER = _package_dir.parent / ".dev-reload-paused"


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
    # Background SDE check: the published dump MD5 at most once per
    # configured interval; a change drop-and-reimports the mirror.
    sde_task = asyncio.create_task(sde_check_loop(settings))
    yield
    sync_task.cancel()
    sde_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await sync_task
        await sde_task
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
    app.include_router(character.router)
    app.include_router(corp.router)
    app.include_router(admin.router)
    app.include_router(structures.router)
    if settings.dev_auto_reload:
        # Dev-only change token that open browsers poll to auto-refresh.
        # Registered only when enabled, so production never serves it.

        @app.get("/__dev/version", include_in_schema=False)
        async def dev_version() -> PlainTextResponse:
            if DEV_PAUSE_MARKER.exists():
                return PlainTextResponse("paused")
            return PlainTextResponse(dev_site_version())

    app.mount("/static", StaticFiles(directory=_package_dir / "static"), name="static")
    return app


app = create_app()
