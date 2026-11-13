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
    # ESI best practices: identify the app so CCP can make contact. Set this
    # in .env to include a real contact address for production use.
    esi_user_agent: str = "industry/0.1 (+https://github.com/blitz-tools/industry)"
    base_url: str = "http://localhost:8000"
    secret_key: str
    database_url: str = "sqlite+aiosqlite:///./industry.db"

    sso_base_url: str = SSO_BASE_URL
    esi_base_url: str = ESI_BASE_URL

    # Asset sync: background interval and page-render knobs.
    assets_sync_interval_minutes: int = 30
    assets_page_size: int = 50
    # Restricted structures (ESI 403) are not retried for this many days —
    # every 403 burns ESI's error-limit budget.
    structure_retry_days: int = 7

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
