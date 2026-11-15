"""Main-character role gating for corporation access.

The main character's tokens stand in for the corporation on corp-scoped
ESI calls, which only works while the main holds a Director or CEO role.
Checking before any corp endpoint is synced follows the same rule as the
rest of the app: a call we know will 403 burns ESI's error-limit budget,
so the grant and the roles are verified first and the UI gets an
explanatory state instead of error spam.
"""

from dataclasses import dataclass, field

from ..models import Character
from .client import ESIClient, ESIError, ReauthorizationRequired

# Scope gating /characters/{id}/roles/ itself (registered on the portal
# 2026-11-15; grants older than that don't hold it yet).
ROLES_SCOPE = "esi-characters.read_corporation_roles.v1"

# Roles that authorize corp-scoped calls. Director grants everything;
# CEO is the fallback for a one-person corp.
GATING_ROLES = frozenset({"Director", "CEO"})


@dataclass
class CorpAccess:
    """Outcome of the main-character gate check.

    status: "ok" (Director/CEO confirmed — corp endpoints authorized),
    "no-main" (no main selected), "no-scope" (grant predates the roles
    scope; a re-auth picks it up), "reauth" (dead refresh token),
    "insufficient" (roles known, no Director/CEO among them), "error".
    """

    status: str
    roles: list[str] = field(default_factory=list)
    detail: str | None = None

    @property
    def authorized(self) -> bool:
        return self.status == "ok"


def has_roles_scope(character: Character) -> bool:
    return ROLES_SCOPE in character.scopes.split()


async def check_corp_access(esi: ESIClient, character: Character) -> CorpAccess:
    """Verify the main can stand in for their corporation. Never raises;
    every failure mode maps to an explanatory status for the UI."""
    if not has_roles_scope(character):
        return CorpAccess("no-scope")
    try:
        body = await esi.get(character, "/characters/{character_id}/roles/")
    except ReauthorizationRequired:
        return CorpAccess("reauth")
    except ESIError as exc:
        return CorpAccess("error", detail=str(exc))
    # The corp-wide roles list carries Director/CEO; the roles_at_* lists
    # are per-location grants that don't authorize the endpoints we use.
    roles = sorted(body.get("roles") or [])
    if GATING_ROLES & set(roles):
        return CorpAccess("ok", roles=roles)
    return CorpAccess("insufficient", roles=roles)
