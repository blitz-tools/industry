"""FastAPI dependencies."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .esi.client import ESIClient


def get_http(request: Request) -> AsyncClient:
    """The shared httpx client created by the app lifespan."""
    return request.app.state.http


def get_session_factory(request: Request):
    return request.app.state.session_factory


async def get_db(
    session_factory: Annotated[async_sessionmaker, Depends(get_session_factory)],
) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


def get_esi_client(
    request: Request, db: Annotated[AsyncSession, Depends(get_db)]
) -> ESIClient:
    settings = request.app.state.settings
    return ESIClient(request.app.state.http, settings, db)


def is_authenticated(request: Request) -> bool:
    """True once any character has been authorized in this browser session."""
    return bool(request.session.get("authenticated"))


HttpDep = Annotated[AsyncClient, Depends(get_http)]
DbDep = Annotated[AsyncSession, Depends(get_db)]
EsiDep = Annotated[ESIClient, Depends(get_esi_client)]
