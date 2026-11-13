"""Application factory."""

from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .config import Settings, get_settings
from .db import make_engine, make_session_factory
from .routes import auth, web

_package_dir = Path(__file__).parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = app.state.settings
    app.state.http = httpx.AsyncClient(timeout=10.0)
    engine = make_engine(settings.database_url)
    app.state.session_factory = make_session_factory(engine)
    yield
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
    app.mount("/static", StaticFiles(directory=_package_dir / "static"), name="static")
    return app


app = create_app()
