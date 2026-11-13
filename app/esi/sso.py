"""EVE SSO (login.eveonline.com) OAuth client — pure HTTP, no database.

Confidential-client authorization-code flow. All token-endpoint calls
authenticate with HTTP Basic per CCP's requirements.
"""

from datetime import UTC, datetime
from typing import Any

import httpx
import jwt
from pydantic import BaseModel

from ..config import Settings


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int


class CharacterClaims(BaseModel):
    """Claims from the SSO v2 access-token JWT."""

    character_id: int
    name: str
    owner_hash: str
    scopes: list[str]
    expires_at: datetime


class SSOError(Exception):
    """SSO request failed (non-200 or transport error)."""


class SSOTokenError(SSOError):
    """Token endpoint returned a non-200 response."""

    def __init__(self, message: str, *, status_code: int):
        super().__init__(message)
        self.status_code = status_code


class SSOClient:
    def __init__(self, http: httpx.AsyncClient, settings: Settings):
        self._http = http
        self._settings = settings

    @property
    def _auth(self) -> tuple[str, str]:
        return (self._settings.esi_client_id, self._settings.esi_client_secret)

    def authorize_url(self, state: str) -> str:
        """Browser redirect target that starts the authorization-code flow."""
        params = {
            "response_type": "code",
            "redirect_uri": self._settings.esi_callback_url,
            "client_id": self._settings.esi_client_id,
            "scope": self._settings.scopes_param,
            "state": state,
        }
        return str(
            httpx.URL(f"{self._settings.sso_base_url}/v2/oauth/authorize", params=params)
        )

    async def exchange_code(self, code: str) -> TokenResponse:
        """Exchange an authorization code for the first token set."""
        data = {
            "grant_type": "authorization_code",
            "code": code,
            # Must be byte-identical to the registered callback URL.
            "redirect_uri": self._settings.esi_callback_url,
        }
        return TokenResponse(**await self._token_request(data))

    async def refresh(self, refresh_token: str) -> TokenResponse:
        """Refresh an access token. SSO v2 ROTATES the refresh token — the
        caller must persist the new refresh_token from the response."""
        data = {"grant_type": "refresh_token", "refresh_token": refresh_token}
        return TokenResponse(**await self._token_request(data))

    async def revoke(self, token: str, *, token_type: str = "refresh_token") -> None:
        """Best-effort token revocation; errors are the caller's problem."""
        response = await self._http.post(
            f"{self._settings.sso_base_url}/v2/oauth/revoke",
            data={"token": token, "token_type_hint": token_type},
            auth=self._auth,
        )
        if response.status_code not in (200, 400, 401):
            raise SSOError(f"revoke failed: {response.status_code}")

    async def _token_request(self, data: dict[str, str]) -> dict[str, Any]:
        try:
            response = await self._http.post(
                f"{self._settings.sso_base_url}/v2/oauth/token",
                data=data,
                auth=self._auth,
            )
        except httpx.HTTPError as exc:
            raise SSOError(f"token endpoint unreachable: {exc}") from exc
        if response.status_code != 200:
            try:
                error = response.json().get("error", response.text[:200])
            except ValueError:
                error = response.text[:200]
            raise SSOTokenError(
                f"token endpoint returned {response.status_code}: {error}",
                status_code=response.status_code,
            )
        return response.json()


def decode_access_token(token: str) -> CharacterClaims:
    """Decode the SSO v2 access-token JWT into character claims.

    The token arrives directly from the token endpoint over TLS, so there is
    no substitution window signature verification would close — CCP's
    third-party development docs bless local unverified decoding. We still
    check exp so stale tokens fail loudly.
    """
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": True},
            # PyJWT requires algorithms even with verification off; the header
            # algorithm (ES256 for SSO v2) is not consulted for decoding.
            algorithms=["ES256"],
        )
    except jwt.PyJWTError as exc:
        raise SSOError(f"invalid access token: {exc}") from exc
    sub = payload["sub"]  # "CHARACTER:EVE:<character_id>"
    prefix = "CHARACTER:EVE:"
    if not isinstance(sub, str) or not sub.startswith(prefix):
        raise SSOError(f"unexpected sub claim: {sub!r}")
    scopes = payload.get("scp", [])
    if isinstance(scopes, str):  # single-scope tokens get a bare string
        scopes = [scopes]
    return CharacterClaims(
        character_id=int(sub.removeprefix(prefix)),
        name=payload["name"],
        owner_hash=payload["owner"],
        scopes=list(scopes),
        expires_at=datetime.fromtimestamp(payload["exp"], tz=UTC).replace(tzinfo=None),
    )
