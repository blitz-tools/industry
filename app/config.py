"""Application settings loaded from environment / .env."""

from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# EVE SSO v2 endpoints (overridable for tests).
SSO_BASE_URL = "https://login.eveonline.com"
ESI_BASE_URL = "https://esi.evetech.net/latest"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    esi_client_id: str
    esi_client_secret: str
    esi_callback_url: str = "http://localhost:8000/auth/eve/callback"
    # NoDecode: env/dotenv values are space-separated, not JSON — the
    # validator below does the splitting.
    esi_scopes: Annotated[list[str], NoDecode] = ["publicData"]
    base_url: str = "http://localhost:8000"
    secret_key: str
    database_url: str = "sqlite+aiosqlite:///./industry.db"

    sso_base_url: str = SSO_BASE_URL
    esi_base_url: str = ESI_BASE_URL

    @field_validator("esi_scopes", mode="before")
    @classmethod
    def _parse_scopes(cls, value: str | list[str]) -> list[str]:
        """Accept a space-separated scope string from the environment."""
        if isinstance(value, str):
            return value.split()
        return value

    @property
    def scopes_param(self) -> str:
        """Scopes as the space-separated string the SSO authorize URL expects."""
        return " ".join(self.esi_scopes)


@lru_cache
def get_settings() -> Settings:
    return Settings()
