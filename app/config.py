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
    # Public world-state syncs (cost indices, market prices): their own
    # background loop — the character-sync tick early-returns on an empty
    # roster, and public data must sync regardless. ETag revalidation
    # makes frequent ticks near-free.
    world_sync_interval_minutes: int = 60
    # Build-plan progress refresh (M6): the materialization tick over
    # non-abandoned plans — DB-only reads (availability, correlation,
    # delivery), so a shorter cadence than the asset sync is cheap.
    plans_refresh_interval_minutes: int = 5
    # SDE import source (python -m app.sde import): fuzzwork's gzipped
    # SQLite dump of the latest Tranquility release, at a stable URL.
    sde_dump_url: str = "https://www.fuzzwork.co.uk/dump/latest-sqlite.db.gz"
    # Background SDE check cadence (admin section): the published MD5 is
    # compared at most this often; a changed hash triggers a full
    # drop-and-reimport of the mirror.
    sde_check_interval_hours: int = 24
    # Restricted structures (ESI 403) are not retried for this many days —
    # every 403 burns ESI's error-limit budget.
    structure_retry_days: int = 7
    # Dev-only (set by compose.dev.yml): open browsers auto-refresh when
    # site files change. Never enable in production.
    dev_auto_reload: bool = False

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
