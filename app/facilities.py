"""Facility registry data layer (M3): the structure/registration
constants the planner multiplies against, security classification, and
the registry's read/validate helpers.

The multiplier values are DATA, pinned with provenance — a CCP balance
pass is a table edit here, never a code change elsewhere:

- Hull bonuses: live ESI dogma 2026-11-23 (strEngTimeBonus /
  strEngMatBonus / strEngCostBonus on Raitaru/Azbel/Sotiyo;
  strReactionTimeMultiplier on the Tatara; the Athanor carries no
  reaction-time bonus).
- Rig base values: live ESI dogma 2026-11-23 (attributeEngRigMatBonus
  −2.0/−2.4, attributeEngRigTimeBonus −20/−24; refinery
  RefRigMatBonus/RefRigTimeBonus identical; the Invention Accelerator
  rigs carry the same time values).
- Security scaling of rig effectiveness: live ESI dogma attributes
  2355/2356/2357 (hiSecModifier/lowSecModifier/nullSecModifier),
  cross-confirmed by everef's database and fuzzwork's calculator.
  Engineering-complex rigs scale ×1.0/×1.9/×2.1; refinery reactor rigs
  scale ×1.0 low / ×1.1 null and carry no highsec modifier (reactions
  cannot run in highsec). The family split was caught on re-verification
  — a first pass applying the EC factors to reactor rigs was wrong.

Two structural discoveries recorded for M4 (2026-11-23): structure rigs
are **per material category** ("Basic Large Ship", "Equipment",
"Advanced Component", … each with Material/Time variants) — the
registry's single-tier rig fields are a deliberate simplification; and
**supercapital construction requires sovereignty plus the
"Supercapital Construction Facilities" infrastructure-hub upgrade**
(two independent sources) — stronger than the nullsec-only working
assumption; the capability flag stays structure-level and curated.
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .esi.client import ESIClient
from .models import Structure, StructureRegistration, UniverseLocation

# --- Registry vocabulary ----------------------------------------------------

# Keys are stored; labels display. Sizes: Raitaru/Athanor medium,
# Azbel/Tatara large, Sotiyo x-large.
STRUCTURE_TYPES: dict[str, str] = {
    "station": "NPC station",
    "raitaru": "Raitaru (medium EC)",
    "azbel": "Azbel (large EC)",
    "sotiyo": "Sotiyo (x-large EC)",
    "athanor": "Athanor (medium refinery)",
    "tatara": "Tatara (large refinery)",
}

ENGINEERING_COMPLEXES = frozenset({"raitaru", "azbel", "sotiyo"})

# Copying joined the spec's three-activity enum (decided at
# implementation, 2026-11-23): the planner's Plan-facilities section
# gives copying its own selector defaulting to the invention default,
# so a distinct registration lets copy jobs point elsewhere without
# affecting invention. Reactions are structure-only — no NPC stations.
ACTIVITIES: tuple[str, ...] = ("manufacturing", "copying", "invention", "reactions")

ACTIVITY_LABELS: dict[str, str] = {
    "manufacturing": "Manufacturing",
    "copying": "Copying",
    "invention": "Invention",
    "reactions": "Reactions",
}

ACTIVITY_STRUCTURE_TYPES: dict[str, tuple[str, ...]] = {
    "manufacturing": ("station", "raitaru", "azbel", "sotiyo"),
    "copying": ("station", "raitaru", "azbel", "sotiyo"),
    "invention": ("station", "raitaru", "azbel", "sotiyo"),
    "reactions": ("athanor", "tatara"),
}

RIG_TIERS: dict[str, str] = {"none": "No rig", "t1": "T1", "t2": "T2"}

# Which rig fields an activity uses. Manufacturing and reactions carry
# both (material + time); invention's time rig is the Invention
# Accelerator; copying has no rig effect in the data.
ACTIVITY_RIG_FIELDS: dict[str, tuple[str, ...]] = {
    "manufacturing": ("me", "te"),
    "reactions": ("me", "te"),
    "invention": ("te",),
    "copying": (),
}

SECURITY_CLASSES: dict[str, str] = {
    "high": "highsec",
    "low": "lowsec",
    "null": "nullsec",
}


def classify_security(security_status: float) -> str:
    """ESI's numeric system security → the class rigs and facility
    rules care about (highsec 0.5+, lowsec above 0, nullsec at 0.0 and
    below — wormholes classify as nullsec)."""
    if security_status >= 0.5:
        return "high"
    if security_status > 0:
        return "low"
    return "null"


# --- Multipliers (the lookup layer M4 reads) ---------------------------------

# Hull bonuses as multipliers (0.85 = −15%), pinned per module docstring.
HULL_BONUSES: dict[str, dict[str, float]] = {
    "station": {},
    "raitaru": {"time": 0.85, "material": 0.99, "cost": 0.97},
    "azbel": {"time": 0.80, "material": 0.99, "cost": 0.96},
    "sotiyo": {"time": 0.70, "material": 0.99, "cost": 0.95},
    "athanor": {},
    "tatara": {"reaction_time": 0.75},
}

# Rig base reductions in percent, before security scaling.
RIG_BASE_PERCENT: dict[tuple[str, str], dict[str, float]] = {
    ("manufacturing", "me"): {"t1": 2.0, "t2": 2.4},
    ("manufacturing", "te"): {"t1": 20.0, "t2": 24.0},
    ("invention", "te"): {"t1": 20.0, "t2": 24.0},
    ("reactions", "me"): {"t1": 2.0, "t2": 2.4},
    ("reactions", "te"): {"t1": 20.0, "t2": 24.0},
}

# Rig effectiveness scales with system security class — differently by
# rig family (live ESI dogma attributes 2355/2356/2357 —
# hiSecModifier/lowSecModifier/nullSecModifier — cross-confirmed by
# everef's database and fuzzwork's calculator): engineering-complex
# rigs ×1.0/×1.9/×2.1; refinery reactor rigs ×1.0 low / ×1.1 null with
# no highsec modifier (reactions cannot run in highsec — a hisec
# refinery registers for reprocessing, not reactors).
SECURITY_RIG_FACTOR: dict[str, dict[str, float]] = {
    "manufacturing": {"high": 1.0, "low": 1.9, "null": 2.1},
    "copying": {},
    "invention": {"high": 1.0, "low": 1.9, "null": 2.1},
    "reactions": {"low": 1.0, "null": 1.1},
}


def effective_rig_percent(activity: str, field: str, tier: str, security: str) -> float:
    """A rig tier's actual reduction at a security class (base × the
    activity's security factor; no rig, no factor for the class, or no
    security known → 0)."""
    base = RIG_BASE_PERCENT.get((activity, field), {}).get(tier, 0.0)
    if not base:
        return 0.0
    factor = SECURITY_RIG_FACTOR.get(activity, {}).get(security, 1.0)
    return base * factor


# --- Registry reads -----------------------------------------------------------


@dataclass
class RegistrationRow:
    """One registry row: a structure's registration for an activity,
    with the structure-level facts denormalized for the grouped
    table."""

    registration_id: int
    structure_id: int
    activity: str
    structure_name: str
    structure_type: str
    system_name: str | None
    security_class: str | None
    me_rig: str
    te_rig: str
    tax_rate: float | None
    is_default: bool
    supercapital_assembly: bool


@dataclass
class ImportCandidate:
    """A player structure the asset sync has observed but that isn't
    registered (the import card). Restricted sightings stay listed but
    carry no usable name or system."""

    location_id: int
    name: str | None
    system_name: str | None
    restricted: bool


async def registration_rows(db: AsyncSession) -> list[RegistrationRow]:
    """Every registration with its structure, name-ordered within each
    activity group."""
    rows = (
        await db.execute(
            select(StructureRegistration, Structure)
            .join(Structure, Structure.id == StructureRegistration.structure_id)
            .order_by(
                StructureRegistration.activity,
                Structure.name,
                Structure.id,
            )
        )
    ).all()
    return [
        RegistrationRow(
            registration_id=registration.id,
            structure_id=structure.id,
            activity=registration.activity,
            structure_name=structure.name,
            structure_type=structure.structure_type,
            system_name=structure.system_name,
            security_class=structure.security_class,
            me_rig=registration.me_rig,
            te_rig=registration.te_rig,
            tax_rate=registration.tax_rate,
            is_default=registration.is_default,
            supercapital_assembly=structure.supercapital_assembly,
        )
        for registration, structure in rows
    ]


async def import_candidates(db: AsyncSession) -> list[ImportCandidate]:
    """Seen-in-sync structures not yet registered. Structures without
    industry lines (market hubs) are indistinguishable in the data —
    they stay importable; the owner decides what registers (market hubs
    belong to the M15 market manager, not here)."""
    structure_rows = (
        await db.execute(
            select(UniverseLocation)
            .where(UniverseLocation.kind == "structure")
            .order_by(UniverseLocation.name)
        )
    ).scalars().all()
    registered = set(
        (
            await db.execute(
                select(Structure.location_id).where(Structure.location_id.is_not(None))
            )
        ).scalars()
    )
    system_rows = (
        await db.execute(
            select(UniverseLocation.location_id, UniverseLocation.name).where(
                UniverseLocation.kind == "solar_system"
            )
        )
    ).all()
    system_names = dict(system_rows)
    candidates: list[ImportCandidate] = []
    for location in structure_rows:
        if location.location_id in registered:
            continue
        candidates.append(
            ImportCandidate(
                location_id=location.location_id,
                name=None if location.restricted else location.name,
                system_name=system_names.get(location.system_id)
                if location.system_id
                else None,
                restricted=location.restricted,
            )
        )
    return candidates


async def system_suggestions(
    db: AsyncSession, query: str, *, limit: int = 8
) -> list[dict]:
    """Type-ahead over the systems the app has resolved (local only —
    ESI's /search/ route is gone, so systems outside the synced
    footprint can't be suggested yet; entering them lands when a sync
    observes them, a recorded limitation)."""
    pattern = f"{query.strip()}%"
    rows = (
        await db.execute(
            select(
                UniverseLocation.location_id,
                UniverseLocation.name,
            )
            .where(
                UniverseLocation.kind == "solar_system",
                UniverseLocation.name.ilike(pattern),
            )
            .order_by(UniverseLocation.name)
            .limit(limit)
        )
    ).all()
    return [{"system_id": system_id, "name": name} for system_id, name in rows]


async def resolve_system(
    db: AsyncSession, esi: ESIClient, system_id: int
) -> tuple[str | None, str | None] | None:
    """(name, security_class) for a system id: ESI's system endpoint
    (public, ETag-cached) first, the local universe_locations row as
    fallback when ESI is unreachable (the local row has no security —
    the class then stays unset). None when neither source knows the
    id."""
    try:
        body = await esi.get_public(f"/universe/systems/{system_id}/")
    except Exception:
        body = None
    if body is not None and body.get("name"):
        return body["name"], classify_security(float(body.get("security_status", 0.0)))
    local = (
        await db.execute(
            select(UniverseLocation).where(
                UniverseLocation.location_id == system_id,
                UniverseLocation.kind == "solar_system",
            )
        )
    ).scalar_one_or_none()
    if local is not None:
        return local.name, None
    return None
