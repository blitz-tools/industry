"""ORM models."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base, TimestampMixin, utc_now


class Character(Base, TimestampMixin):
    """An authorized EVE character and its current SSO tokens.

    One row per character, across any number of EVE accounts. Refresh-token
    rotation replaces the token set in place, so tokens live inline. A changed
    owner_hash means the character was transferred and old tokens are void.
    """

    __tablename__ = "characters"

    character_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    owner_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    scopes: Mapped[str] = mapped_column(Text, nullable=False)
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    access_token_expires_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=utc_now
    )
    refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
