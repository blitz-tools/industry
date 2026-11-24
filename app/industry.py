"""Industry data view layer: pure DB reads for the blueprint, job, and
skill pages (character and corporation). The planner (M4+) builds on
these joins — blueprints carry ME/TE/runs the planner multiplies against,
jobs carry the activity ids that join the SDE, skills feed time math and
slot ceilings.
"""

from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import String, and_, bindparam, cast, func, literal, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from .esi.assets import (
    KIND_CHAR_SKILLS,
    OFFICE_FLAGS,
    OFFICE_TYPE_ID,
    OWNER_CHARACTER,
    OWNER_CORPORATION,
)
from .models import (
    Asset,
    Blueprint,
    Character,
    CostIndex,
    DataSync,
    IndustryJob,
    MarketPrice,
    Skill,
    UniverseLocation,
    UniverseType,
)

# ramActivities ids (the SDE is the authority once M2 lands; this covers
# everything ESI reports today).
ACTIVITY_LABELS = {
    1: "Manufacturing",
    2: "Research (Tech)",
    3: "Research TE",
    4: "Research ME",
    5: "Copying",
    7: "Duplication",
    8: "Invention",
    9: "Reactions",
}

# Job statuses that occupy a slot or await delivery; the history toggle
# adds the terminal ones (delivered, cancelled, reverted).
ACTIVE_JOB_STATUSES = frozenset({"active", "paused", "ready"})

# Status → badge color class on the jobs table.
JOB_STATUS_CLASSES = {
    "active": "ok",
    "ready": "ok",
    "paused": "warn",
    "delivered": "done",
    "cancelled": "failed",
    "reverted": "failed",
}

# Roman numerals for skill levels (EVE training caps at V).
SKILL_LEVELS = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}


@dataclass
class BlueprintRow:
    item_id: int
    type_id: int
    type_name: str | None
    # Imageserver render: originals ("bp") and copies ("bpc") need their
    # dedicated blueprint endpoints (see templates.type_icon_url).
    icon_kind: str
    material_efficiency: int
    time_efficiency: int
    runs: int | None  # -1 marks an original (unlimited runs)
    # Resolved name; ESI's quantity is a sentinel (-2 copy, -1/1 original)
    # and never a real count, so it is not carried.
    location_name: str
    location_flag: str
    # Owning character's name; None on single-owner (corporation) views.
    owner_name: str | None = None

    @property
    def is_original(self) -> bool:
        return self.runs == -1 or self.runs is None


@dataclass
class JobRow:
    job_id: int
    activity: str
    blueprint_type_id: int
    blueprint_type_name: str | None
    installer_name: str | None  # None: not one of the tracked characters
    installer_id: int
    runs: int
    successful_runs: int | None
    status: str
    start_date: datetime | None
    end_date: datetime | None
    # Owning character's name; None on single-owner (corporation) views.
    owner_name: str | None = None

    @property
    def status_class(self) -> str:
        return JOB_STATUS_CLASSES.get(self.status, "warn")


@dataclass
class SkillRow:
    skill_id: int
    name: str | None
    trained_level: int
    active_level: int  # includes implant/booster effects
    skillpoints: int

    @property
    def trained_roman(self) -> str:
        return SKILL_LEVELS.get(self.trained_level, str(self.trained_level))

    @property
    def active_roman(self) -> str:
        return SKILL_LEVELS.get(self.active_level, str(self.active_level))


@dataclass
class SkillSummary:
    """One character's skill sheet at a glance (the skills page's default
    view); counts and total SP read 0 before the first sync."""

    character: Character
    skill_count: int
    total_sp: int
    status: str | None  # None = never synced
    detail: str | None
    synced_at: datetime | None


async def blueprints_page(
    db: AsyncSession,
    *,
    owner_type: str,
    owner_ids: list[int] | None,
    page: int,
    page_size: int,
) -> tuple[list[BlueprintRow], int, int]:
    """One page of an owner set's blueprints, name-ordered. Location names
    come from the universe cache (asset syncs populate it); unknown
    locations read as None and the template falls back to the raw id.
    `owner_ids` None means every owner of that type."""
    conditions = [Blueprint.owner_type == owner_type]
    if owner_ids is not None:
        conditions.append(Blueprint.owner_id.in_(owner_ids))
    # Count with the same join the rows use: the character view's inner
    # Character join hides orphaned owner ids (a forgotten character's
    # leftovers), and a count that includes them would disagree with the
    # rendered rows and the pagination boundaries.
    count_query = select(func.count()).select_from(Blueprint).where(*conditions)
    if owner_type == OWNER_CHARACTER:
        count_query = count_query.join(
            Character, Character.character_id == Blueprint.owner_id
        )
    total = (await db.execute(count_query)).scalar_one()
    pages = max(1, -(-total // page_size))
    page = min(max(1, page), pages)

    type_name = func.coalesce(
        UniverseType.name, "#" + cast(Blueprint.type_id, String)
    )
    # A blueprint's location_id may be a station/structure — or the item
    # id of the office/container it sits in (ESI reports office contents
    # against the office item itself). The owner's asset snapshot provides
    # the hop: item id → its denormalized top-level parent location.
    parent_location = aliased(UniverseLocation)
    location_name = func.coalesce(
        UniverseLocation.name,
        parent_location.name,
        "#" + cast(Blueprint.location_id, String),
    )
    # The character view can span several owners, so it selects and groups
    # by the owner's name (characters always resolve — rows only exist for
    # stored characters — so the join is inner); the single-owner
    # corporation view selects a NULL instead of joining.
    owner_char = aliased(Character)
    multi_owner = owner_type == OWNER_CHARACTER
    owner_name = owner_char.name if multi_owner else literal(None)
    columns = [
        Blueprint.item_id,
        Blueprint.type_id,
        UniverseType.name,
        Blueprint.material_efficiency,
        Blueprint.time_efficiency,
        Blueprint.runs,
        location_name,
        Blueprint.location_flag,
        owner_name,
    ]
    order = [owner_name, type_name, Blueprint.item_id] if multi_owner else [
        type_name, Blueprint.item_id
    ]
    query = (
        select(*columns)
        .outerjoin(UniverseType, UniverseType.type_id == Blueprint.type_id)
        .outerjoin(
            UniverseLocation, UniverseLocation.location_id == Blueprint.location_id
        )
        .outerjoin(
            Asset,
            and_(
                Asset.owner_type == owner_type,
                Asset.owner_id == Blueprint.owner_id,
                Asset.item_id == Blueprint.location_id,
            ),
        )
        .outerjoin(
            parent_location,
            parent_location.location_id == Asset.parent_location_id,
        )
    )
    if multi_owner:
        query = query.join(owner_char, owner_char.character_id == Blueprint.owner_id)
    rows_raw = (
        await db.execute(
            query.where(*conditions)
            .order_by(*order)
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
    ).all()
    rows = [
        BlueprintRow(
            item_id=item_id,
            type_id=type_id,
            type_name=name or f"Unknown type #{type_id}",
            icon_kind="bp" if runs in (-1, None) else "bpc",
            material_efficiency=me,
            time_efficiency=te,
            runs=runs,
            location_name=loc_name,
            location_flag=flag,
            owner_name=owner,
        )
        for (item_id, type_id, name, me, te, runs, loc_name, flag, owner) in rows_raw
    ]
    return rows, total, page


async def corporation_blueprints(
    db: AsyncSession, corporation_id: int, *, page: int, page_size: int
) -> tuple[list[BlueprintRow], int, int]:
    """One page of the corporation's blueprints (single-owner view)."""
    return await blueprints_page(
        db,
        owner_type=OWNER_CORPORATION,
        owner_ids=[corporation_id],
        page=page,
        page_size=page_size,
    )


async def jobs_page(
    db: AsyncSession,
    *,
    owner_type: str,
    owner_ids: list[int] | None,
    include_completed: bool,
    page: int,
    page_size: int,
) -> tuple[list[JobRow], int, int]:
    """One page of an owner set's industry jobs, newest first. Installers
    resolve through the tracked characters (the common case); anyone else
    reads as their raw character id. `owner_ids` None means every owner of
    that type."""
    conditions = [IndustryJob.owner_type == owner_type]
    if owner_ids is not None:
        conditions.append(IndustryJob.owner_id.in_(owner_ids))
    if not include_completed:
        conditions.append(IndustryJob.status.in_(ACTIVE_JOB_STATUSES))
    # Same join-symmetry rule as blueprints_page: the count matches the
    # row query's inner Character join in the character view.
    count_query = select(func.count()).select_from(IndustryJob).where(*conditions)
    if owner_type == OWNER_CHARACTER:
        count_query = count_query.join(
            Character, Character.character_id == IndustryJob.owner_id
        )
    total = (await db.execute(count_query)).scalar_one()
    pages = max(1, -(-total // page_size))
    page = min(max(1, page), pages)

    installer = aliased(Character)
    owner_char = aliased(Character)
    # See blueprints_page: the character view spans owners and groups by
    # the owner's name; the corporation view selects a NULL.
    multi_owner = owner_type == OWNER_CHARACTER
    owner_name = owner_char.name if multi_owner else literal(None)
    columns = [
        IndustryJob.job_id,
        IndustryJob.activity_id,
        IndustryJob.blueprint_type_id,
        UniverseType.name,
        installer.name,
        IndustryJob.installer_id,
        IndustryJob.runs,
        IndustryJob.successful_runs,
        IndustryJob.status,
        IndustryJob.start_date,
        IndustryJob.end_date,
        owner_name,
    ]
    query = (
        select(*columns)
        .outerjoin(
            UniverseType, UniverseType.type_id == IndustryJob.blueprint_type_id
        )
        .outerjoin(installer, installer.character_id == IndustryJob.installer_id)
    )
    order = [
        owner_name,
        IndustryJob.start_date.desc().nulls_last(),
        IndustryJob.job_id,
    ] if multi_owner else [
        IndustryJob.start_date.desc().nulls_last(),
        IndustryJob.job_id,
    ]
    if multi_owner:
        query = query.join(owner_char, owner_char.character_id == IndustryJob.owner_id)
    rows_raw = (
        await db.execute(
            query.where(*conditions)
            .order_by(*order)
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
    ).all()
    rows = [
        JobRow(
            job_id=job_id,
            activity=ACTIVITY_LABELS.get(activity_id, f"Activity #{activity_id}"),
            blueprint_type_id=blueprint_type_id,
            blueprint_type_name=name or f"Unknown type #{blueprint_type_id}",
            installer_name=installer_name,
            installer_id=installer_id,
            runs=runs,
            successful_runs=successful_runs,
            status=status,
            start_date=start_date,
            end_date=end_date,
            owner_name=owner,
        )
        for (
            job_id,
            activity_id,
            blueprint_type_id,
            name,
            installer_name,
            installer_id,
            runs,
            successful_runs,
            status,
            start_date,
            end_date,
            owner,
        ) in rows_raw
    ]
    return rows, total, page


async def corporation_jobs(
    db: AsyncSession,
    corporation_id: int,
    *,
    include_completed: bool,
    page: int,
    page_size: int,
) -> tuple[list[JobRow], int, int]:
    """One page of the corporation's industry jobs (single-owner view)."""
    return await jobs_page(
        db,
        owner_type=OWNER_CORPORATION,
        owner_ids=[corporation_id],
        include_completed=include_completed,
        page=page,
        page_size=page_size,
    )


async def character_skills(
    db: AsyncSession, character_id: int, *, page: int, page_size: int
) -> tuple[list[SkillRow], int, int]:
    """One page of a character's skill sheet, name-ordered. Skill names
    come from the universe cache (the skills sync populates it); unknown
    skills read as None and the template falls back to the raw id."""
    conditions = [
        Skill.owner_type == OWNER_CHARACTER,
        Skill.owner_id == character_id,
    ]
    total = (
        await db.execute(select(func.count()).select_from(Skill).where(*conditions))
    ).scalar_one()
    pages = max(1, -(-total // page_size))
    page = min(max(1, page), pages)

    skill_name = func.coalesce(UniverseType.name, "#" + cast(Skill.skill_id, String))
    rows_raw = (
        await db.execute(
            select(
                Skill.skill_id,
                UniverseType.name,
                Skill.trained_skill_level,
                Skill.active_skill_level,
                Skill.skillpoints_in_skill,
            )
            .outerjoin(UniverseType, UniverseType.type_id == Skill.skill_id)
            .where(*conditions)
            .order_by(skill_name, Skill.skill_id)
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
    ).all()
    rows = [
        SkillRow(
            skill_id=skill_id,
            name=name or f"Unknown skill #{skill_id}",
            trained_level=trained,
            active_level=active,
            skillpoints=skillpoints,
        )
        for (skill_id, name, trained, active, skillpoints) in rows_raw
    ]
    return rows, total, page


async def skill_summaries(
    db: AsyncSession, characters: list[Character]
) -> list[SkillSummary]:
    """Per-character skill counts and total SP (0 before the first sync),
    each with its last skills-sync outcome."""
    stats = {
        owner_id: (count, sp or 0)
        for owner_id, count, sp in (
            await db.execute(
                select(
                    Skill.owner_id,
                    func.count(),
                    func.sum(Skill.skillpoints_in_skill),
                )
                .where(Skill.owner_type == OWNER_CHARACTER)
                .group_by(Skill.owner_id)
            )
        ).all()
    }
    syncs = {
        sync.owner_id: sync
        for sync in (
            await db.execute(
                select(DataSync).where(
                    DataSync.kind == KIND_CHAR_SKILLS,
                    DataSync.owner_type == OWNER_CHARACTER,
                )
            )
        ).scalars()
    }
    return [
        SkillSummary(
            character=character,
            skill_count=stats.get(character.character_id, (0, 0))[0],
            total_sp=stats.get(character.character_id, (0, 0))[1],
            status=sync.status if (sync := syncs.get(character.character_id)) else None,
            detail=sync.detail if sync else None,
            synced_at=sync.synced_at if sync else None,
        )
        for character in characters
    ]


async def character_sync_notes(
    db: AsyncSession,
    kind: str,
    characters: list[Character],
    selected: list[int] | None,
) -> tuple[list[tuple[str, str]], datetime | None]:
    """(notes, last attempt) for a per-character data kind across the
    characters in scope (None = all). Notes surface only problem outcomes —
    a clean pass renders nothing; the page's own empty-state note covers a
    never-synced sheet."""
    ids = (
        [character.character_id for character in characters]
        if selected is None
        else selected
    )
    if not ids:
        return [], None
    syncs = {
        sync.owner_id: sync
        for sync in (
            await db.execute(
                select(DataSync).where(
                    DataSync.kind == kind,
                    DataSync.owner_type == OWNER_CHARACTER,
                    DataSync.owner_id.in_(ids),
                )
            )
        ).scalars()
    }
    names = {character.character_id: character.name for character in characters}
    notes: list[tuple[str, str]] = []
    for owner_id in ids:
        sync = syncs.get(owner_id)
        if sync is None or sync.status == "ok":
            continue
        name = names.get(owner_id, f"Character #{owner_id}")
        if sync.status == "no-scope":
            notes.append(
                (
                    "error",
                    f"{name}'s grant is missing a required scope — re-auth it. "
                    f"{sync.detail or ''}".strip(),
                )
            )
        elif sync.status == "reauth":
            notes.append(("error", f"{name} needs re-authorization."))
        else:
            notes.append(
                ("error", f"{name}: last sync failed — {sync.detail or 'unknown'}")
            )
    last = max((sync.synced_at for sync in syncs.values()), default=None)
    return notes, last


# ---------------------------------------------------------------------------
# Catalog query layer (M2) — commodity search and recipe reads over the SDE
# mirror, plus the owned-blueprint overlay. The M4 planner consumes these;
# the sde_* tables stay verbatim (no ORM models), so everything here is raw
# SQL and every interpretation of the dump lives in this section.
# ---------------------------------------------------------------------------

# The buildable catalog: products of manufacturing (activity 1) and
# reactions. ramActivities labels reactions 9, but the dump's recipe data
# lives on activity 11 (reference/README.md) — labels here speak SDE.
CATALOG_ACTIVITIES = (1, 11)
SDE_ACTIVITY_LABELS = {1: "Manufacturing", 11: "Reaction"}

# Name merge rule (decided here per MILESTONES.md M2): the SDE name is
# authoritative wherever the mirror has the type — the catalog IS the
# mirror, and universe_types is write-once so preferring it would pin
# names at first-sync time (live evidence: one universe name carries a
# trailing space the SDE lacks). universe_types only names ids the dump
# lacks — orphan product rows and SDE release lag — so every coalesce
# below reads SDE first. ESI-synced-id pages (blueprints, jobs, skills)
# keep their existing universe-only resolution.

# Producer selection: the reference model takes a product's first
# industryActivityProducts row (rowid order); on the real mirror that
# picks CCP test artifacts where they sit first (Tungsten Carbide's
# "Test Reaction Blueprint", unpublished). This layer prefers the first
# *published* producer, falling back to the first row when none is
# published (210 products' only producers are unpublished). All ten chain
# anchors have a single published producer, so the golden values are
# unaffected; M5's resolver adopts the same rule.
_PRODUCER_CTE = """
    SELECT p.productTypeID AS product_id,
           p.typeID AS bp_type_id,
           p.activityID AS activity_id,
           p.quantity AS products_per_run,
           ROW_NUMBER() OVER (
               PARTITION BY p.productTypeID
               ORDER BY CASE WHEN bp.published = 1 THEN 0 ELSE 1 END, p.rowid
           ) AS rn
    FROM sde_industryActivityProducts p
    LEFT JOIN sde_invTypes bp ON bp.typeID = p.typeID
    WHERE p.activityID IN (1, 11)
"""


@dataclass
class CatalogEntry:
    """One buildable product in the catalog search (the planner's
    commodity-first autocomplete row): the built commodity, its derived
    producer blueprint, and pool-wide owned-blueprint counts."""

    type_id: int
    type_name: str
    group_name: str | None
    blueprint_type_id: int
    blueprint_name: str
    activity_id: int  # SDE activity (1 manufacturing, 11 reaction)
    products_per_run: int
    max_production_limit: int | None  # None: no industryBlueprints row
    owned_originals: int  # BPOs across the whole pool (corp + characters)
    owned_copies: int

    @property
    def activity_label(self) -> str:
        return SDE_ACTIVITY_LABELS.get(self.activity_id, f"Activity {self.activity_id}")

    @property
    def owned_count(self) -> int:
        return self.owned_originals + self.owned_copies


@dataclass
class RecipeMaterial:
    """One build input per run, flagged for chain continuation (M5's
    recursion signal: the material is itself a catalog product)."""

    type_id: int
    name: str
    quantity_per_run: int
    buildable: bool


@dataclass
class RecipeSkill:
    """One required skill level for the activity. The dump carries exact
    duplicate skill rows; the read dedups."""

    skill_id: int
    name: str
    level: int


@dataclass
class RecipeHeader:
    """One buildable product's producer facts, bulk-read for the chain
    resolver (M5): the prefer-published producer (the same _PRODUCER_CTE
    rule the single-commodity reads use), products per run, max
    production limit, and the activity + copy durations. A type with no
    header row is a chain terminator — absence is the walk's stop
    signal, never an error."""

    type_id: int
    blueprint_type_id: int
    blueprint_name: str
    activity_id: int  # 1 manufacturing, 11 reactions
    products_per_run: int
    max_production_limit: int | None
    duration_seconds: int | None  # None: no industryActivity row
    copy_duration_seconds: int | None  # activity 5; None: not copyable


@dataclass
class ChainMaterial:
    """One per-run build input of a product's producing blueprint, as
    the chain resolver consumes it (bulk-read by product type id — the
    producer choice is already applied by the read)."""

    type_id: int
    quantity_per_run: int


@dataclass
class MaterialSource:
    """One location the coverage measurement can count from (M6's
    Material sources selector): a corp office hangar, a participant's
    personal hangar at one location, or a station container inside a
    corp office hangar. `ref` is the selection identity used in URL
    state and (later) the plan snapshot — "office:<structure id>",
    "hangar:<character id>:<structure id>", "container:<item id>".
    `quantities` holds this source's on-hand stock per measured type.
    Labeling is the view layer's job; this read returns ids only."""

    kind: str  # "office" | "hangar" | "container"
    ref: str
    character_id: int | None  # hangar sources only
    location_id: int | None  # structure/station the source sits at
    container_item_id: int | None = None  # container sources only
    container_type_id: int | None = None  # container sources only (labeling)
    quantities: dict[int, int] = field(default_factory=dict)


@dataclass
class CommodityRecipe:
    """Everything the M4 calculator needs for one selected commodity:
    the producing blueprint, its per-run inputs and skills, the activity
    duration, the per-run copy duration (activity 5 — M4's copy-time
    math), and the owned-blueprint overlay (ME/TE/runs per copy)."""

    type_id: int
    type_name: str
    group_name: str | None
    blueprint_type_id: int
    blueprint_name: str
    activity_id: int
    products_per_run: int
    max_production_limit: int | None
    duration_seconds: int | None  # None: no industryActivity row
    copy_duration_seconds: int | None  # activity 5; None: not copyable
    materials: list[RecipeMaterial]
    skills: list[RecipeSkill]
    owned: list[BlueprintRow]

    @property
    def activity_label(self) -> str:
        return SDE_ACTIVITY_LABELS.get(self.activity_id, f"Activity {self.activity_id}")


async def search_catalog(
    db: AsyncSession,
    query: str,
    *,
    limit: int = 10,
    owned_only: bool = False,
) -> list[CatalogEntry]:
    """Name-ordered catalog search over the buildable products
    (products of activities 1 and 11, no published filter — the census
    membership rule; the catalog's size is whatever the current SDE
    release holds and is never referenced as a constant). Prefix
    matches sort first. `owned_only` keeps products with any blueprint
    in the inventory pool (the planner's Match From Inventory
    toggle)."""
    pattern = f"%{query.strip()}%"
    prefix = f"{query.strip()}%"
    owned_filter = (
        "AND EXISTS (SELECT 1 FROM blueprints b WHERE b.type_id = prod.bp_type_id)"
        if owned_only
        else ""
    )
    rows = (
        await db.execute(
            text(
                f"""
                WITH prod AS ({_PRODUCER_CTE})
                SELECT prod.product_id,
                       coalesce(t.typeName, u.name,
                                '#' || prod.product_id) AS type_name,
                       g.groupName AS group_name,
                       prod.bp_type_id,
                       coalesce(bp.typeName, '#' || prod.bp_type_id)
                           AS blueprint_name,
                       prod.activity_id,
                       prod.products_per_run,
                       mpl.maxProductionLimit AS max_production_limit,
                       (SELECT count(*) FROM blueprints b
                         WHERE b.type_id = prod.bp_type_id
                           AND (b.runs = -1 OR b.runs IS NULL)) AS owned_originals,
                       (SELECT count(*) FROM blueprints b
                         WHERE b.type_id = prod.bp_type_id AND b.runs >= 0)
                           AS owned_copies
                FROM prod
                LEFT JOIN sde_invTypes t ON t.typeID = prod.product_id
                LEFT JOIN universe_types u ON u.type_id = prod.product_id
                LEFT JOIN sde_invGroups g ON g.groupID = t.groupID
                LEFT JOIN sde_invTypes bp ON bp.typeID = prod.bp_type_id
                LEFT JOIN sde_industryBlueprints mpl
                       ON mpl.typeID = prod.bp_type_id
                WHERE prod.rn = 1
                  AND coalesce(t.typeName, u.name,
                               '#' || prod.product_id) LIKE :pattern
                  {owned_filter}
                ORDER BY (coalesce(t.typeName, u.name,
                                   '#' || prod.product_id) LIKE :prefix) DESC,
                         coalesce(t.typeName, u.name,
                                  '#' || prod.product_id),
                         prod.product_id
                LIMIT :limit
                """
            ),
            {"pattern": pattern, "prefix": prefix, "limit": limit},
        )
    ).all()
    return [
        CatalogEntry(
            type_id=product_id,
            type_name=type_name,
            group_name=group_name,
            blueprint_type_id=bp_type_id,
            blueprint_name=blueprint_name,
            activity_id=activity_id,
            products_per_run=products_per_run,
            max_production_limit=max_production_limit,
            owned_originals=owned_originals,
            owned_copies=owned_copies,
        )
        for (
            product_id,
            type_name,
            group_name,
            bp_type_id,
            blueprint_name,
            activity_id,
            products_per_run,
            max_production_limit,
            owned_originals,
            owned_copies,
        ) in rows
    ]


async def catalog_size(db: AsyncSession) -> int:
    """The buildable catalog's live size (the census membership rule,
    counted at query time — never referenced as a constant; whatever
    the current SDE release holds)."""
    return (
        await db.execute(
            text(
                f"""
                SELECT count(*) FROM (
                    SELECT DISTINCT p.productTypeID
                    FROM sde_industryActivityProducts p
                    WHERE p.activityID IN {CATALOG_ACTIVITIES}
                )
                """
            )
        )
    ).scalar_one()


async def commodity_recipe(db: AsyncSession, type_id: int) -> CommodityRecipe | None:
    """The full recipe read for one buildable commodity: producer
    blueprint (prefer-published first row), per-run materials flagged for
    chain continuation, deduped skills, duration, max production limit,
    and the owned-blueprint overlay. None when the type is not a catalog
    product (raw, or invention-sourced BPC)."""
    header = (
        await db.execute(
            text(
                f"""
                WITH prod AS ({_PRODUCER_CTE})
                SELECT prod.product_id,
                       coalesce(t.typeName, u.name,
                                '#' || prod.product_id) AS type_name,
                       g.groupName AS group_name,
                       prod.bp_type_id,
                       coalesce(bp.typeName, '#' || prod.bp_type_id)
                           AS blueprint_name,
                       prod.activity_id,
                       prod.products_per_run,
                       mpl.maxProductionLimit AS max_production_limit
                FROM prod
                LEFT JOIN sde_invTypes t ON t.typeID = prod.product_id
                LEFT JOIN universe_types u ON u.type_id = prod.product_id
                LEFT JOIN sde_invGroups g ON g.groupID = t.groupID
                LEFT JOIN sde_invTypes bp ON bp.typeID = prod.bp_type_id
                LEFT JOIN sde_industryBlueprints mpl
                       ON mpl.typeID = prod.bp_type_id
                WHERE prod.rn = 1 AND prod.product_id = :type_id
                """
            ),
            {"type_id": type_id},
        )
    ).first()
    if header is None:
        return None
    (
        product_id,
        type_name,
        group_name,
        bp_type_id,
        blueprint_name,
        activity_id,
        products_per_run,
        max_production_limit,
    ) = header

    duration = (
        await db.execute(
            text(
                "SELECT time FROM sde_industryActivity"
                " WHERE typeID = :bp AND activityID = :activity"
            ),
            {"bp": bp_type_id, "activity": activity_id},
        )
    ).scalar_one_or_none()
    # Per-run copy time (SDE activity 5) for the copy-time math; a
    # blueprint with no copying row is not copyable.
    copy_duration = (
        await db.execute(
            text(
                "SELECT time FROM sde_industryActivity"
                " WHERE typeID = :bp AND activityID = 5"
            ),
            {"bp": bp_type_id},
        )
    ).scalar_one_or_none()

    materials = [
        RecipeMaterial(
            type_id=material_type_id,
            name=name,
            quantity_per_run=quantity,
            buildable=bool(buildable),
        )
        for (material_type_id, name, quantity, buildable) in (
            await db.execute(
                text(
                    """
                    SELECT m.materialTypeID,
                           coalesce(mt.typeName, um.name,
                                    '#' || m.materialTypeID) AS name,
                           m.quantity,
                           EXISTS (
                               SELECT 1 FROM sde_industryActivityProducts p
                                WHERE p.productTypeID = m.materialTypeID
                                  AND p.activityID IN (1, 11)
                           ) AS buildable
                    FROM sde_industryActivityMaterials m
                    LEFT JOIN sde_invTypes mt ON mt.typeID = m.materialTypeID
                    LEFT JOIN universe_types um ON um.type_id = m.materialTypeID
                    WHERE m.typeID = :bp AND m.activityID = :activity
                    ORDER BY m.quantity DESC, name, m.materialTypeID
                    """
                ),
                {"bp": bp_type_id, "activity": activity_id},
            )
        ).all()
    ]

    skills = [
        RecipeSkill(skill_id=skill_id, name=name, level=level)
        for (skill_id, name, level) in (
            await db.execute(
                text(
                    """
                    SELECT DISTINCT s.skillID,
                           coalesce(st.typeName, us.name,
                                    '#' || s.skillID) AS name,
                           s.level
                    FROM sde_industryActivitySkills s
                    LEFT JOIN sde_invTypes st ON st.typeID = s.skillID
                    LEFT JOIN universe_types us ON us.type_id = s.skillID
                    WHERE s.typeID = :bp AND s.activityID = :activity
                    ORDER BY s.level DESC, name, s.skillID
                    """
                ),
                {"bp": bp_type_id, "activity": activity_id},
            )
        ).all()
    ]

    owned = await owned_blueprints_for_type(db, bp_type_id)
    return CommodityRecipe(
        type_id=product_id,
        type_name=type_name,
        group_name=group_name,
        blueprint_type_id=bp_type_id,
        blueprint_name=blueprint_name,
        activity_id=activity_id,
        products_per_run=products_per_run,
        max_production_limit=max_production_limit,
        duration_seconds=duration,
        copy_duration_seconds=copy_duration,
        materials=materials,
        skills=skills,
        owned=owned,
    )


async def owned_blueprints_for_type(
    db: AsyncSession, blueprint_type_id: int
) -> list[BlueprintRow]:
    """Every owned copy of one blueprint type across the whole pool
    (corporation + characters) — the M4 planner's ME/TE pre-fill source.
    Owner names resolve through the tracked characters and the universe
    corporation cache; locations follow the blueprints-page hop rule
    (owner's asset snapshot: item id → top-level parent location)."""
    bulk = await owned_blueprints_for_types(db, [blueprint_type_id])
    return bulk.get(blueprint_type_id, [])


async def owned_blueprints_for_types(
    db: AsyncSession, blueprint_type_ids: list[int]
) -> dict[int, list[BlueprintRow]]:
    """The owned-blueprint overlay for a set of blueprint types, keyed by
    type — the chain-wide availability read (M5) the single-type read
    above delegates to. Same joins and ordering per type."""
    if not blueprint_type_ids:
        return {}
    rows_raw = (
        await db.execute(
            text(
                """
                SELECT b.item_id,
                       b.type_id,
                       coalesce(t.typeName, ut.name, '#' || b.type_id) AS name,
                       b.material_efficiency,
                       b.time_efficiency,
                       b.runs,
                       coalesce(loc.name, parent.name,
                                '#' || b.location_id) AS location_name,
                       b.location_flag,
                       coalesce(ch.name, uc.name) AS owner_name
                FROM blueprints b
                LEFT JOIN sde_invTypes t ON t.typeID = b.type_id
                LEFT JOIN universe_types ut ON ut.type_id = b.type_id
                LEFT JOIN universe_locations loc
                       ON loc.location_id = b.location_id
                LEFT JOIN assets a
                       ON a.owner_type = b.owner_type
                      AND a.owner_id = b.owner_id
                      AND a.item_id = b.location_id
                LEFT JOIN universe_locations parent
                       ON parent.location_id = a.parent_location_id
                LEFT JOIN characters ch
                       ON b.owner_type = :char_kind
                      AND ch.character_id = b.owner_id
                LEFT JOIN universe_corporations uc
                       ON b.owner_type = :corp_kind
                      AND uc.corporation_id = b.owner_id
                WHERE b.type_id IN :blueprint_type_ids
                ORDER BY b.type_id, owner_name, b.item_id
                """
            ).bindparams(bindparam("blueprint_type_ids", expanding=True)),
            {
                "blueprint_type_ids": list(blueprint_type_ids),
                "char_kind": OWNER_CHARACTER,
                "corp_kind": OWNER_CORPORATION,
            },
        )
    ).all()
    grouped: dict[int, list[BlueprintRow]] = {
        type_id: [] for type_id in blueprint_type_ids
    }
    for (item_id, type_id, name, me, te, runs, location_name, flag, owner) in rows_raw:
        grouped.setdefault(type_id, []).append(
            BlueprintRow(
                item_id=item_id,
                type_id=type_id,
                type_name=name or f"Unknown type #{type_id}",
                icon_kind="bp" if runs in (-1, None) else "bpc",
                material_efficiency=me,
                time_efficiency=te,
                runs=runs,
                location_name=location_name,
                location_flag=flag,
                owner_name=owner,
            )
        )
    return grouped


# ---------------------------------------------------------------------------
# Planner read helpers (M4) — skills, world data, and raw-material
# classification. Same layer rules as the catalog section: pure DB reads,
# interpretation lives with the consumer (app/planner.py).
# ---------------------------------------------------------------------------

# Registry activity key → ESI's /industry/systems/ activity string
# (pinned from a live response 2026-11-23: copying, invention,
# manufacturing, reaction, researching_material_efficiency,
# researching_time_efficiency — the mirror stores these verbatim).
COST_INDEX_ACTIVITIES: dict[str, str] = {
    "manufacturing": "manufacturing",
    "copying": "copying",
    "invention": "invention",
    "reactions": "reaction",
}


async def active_skill_levels(
    db: AsyncSession, character_ids: list[int]
) -> dict[int, dict[int, int]]:
    """Active skill levels (implants/boosters included — what gameplay
    math sees, the deliberate M4 pick) for a set of characters, keyed
    {character_id: {skill_id: level}}. Characters with no synced sheet
    simply key an empty dict."""
    if not character_ids:
        return {}
    rows = (
        await db.execute(
            select(Skill.owner_id, Skill.skill_id, Skill.active_skill_level).where(
                Skill.owner_type == OWNER_CHARACTER,
                Skill.owner_id.in_(character_ids),
            )
        )
    ).all()
    levels: dict[int, dict[int, int]] = {cid: {} for cid in character_ids}
    for owner_id, skill_id, level in rows:
        levels[owner_id][skill_id] = level
    return levels


async def adjusted_prices(
    db: AsyncSession, type_ids: list[int]
) -> dict[int, float | None]:
    """Adjusted base prices (ESI /markets/prices/, synced by the world
    band) for a set of types. Types with no synced price (or a null
    adjusted_price) key None — the install-cost math degrades on them
    rather than crashing."""
    if not type_ids:
        return {}
    rows = (
        await db.execute(
            select(MarketPrice.type_id, MarketPrice.adjusted_price).where(
                MarketPrice.type_id.in_(type_ids)
            )
        )
    ).all()
    prices = {type_id: None for type_id in type_ids}
    for type_id, adjusted in rows:
        prices[type_id] = adjusted
    return prices


async def cost_index(
    db: AsyncSession, system_id: int | None, activity_key: str
) -> float | None:
    """One system's cost index for a registry activity key. None when
    the system is unknown or the world band has not synced it — the
    install-cost readout degrades, never crashes."""
    if system_id is None:
        return None
    esi_activity = COST_INDEX_ACTIVITIES.get(activity_key)
    if esi_activity is None:
        return None
    return (
        await db.execute(
            select(CostIndex.cost_index).where(
                CostIndex.system_id == system_id,
                CostIndex.activity == esi_activity,
            )
        )
    ).scalar_one_or_none()


async def material_categories(
    db: AsyncSession, type_ids: list[int]
) -> dict[int, tuple[str | None, str | None]]:
    """(category_name, group_name) for a set of types via the SDE's
    invGroups/invCategories — the raw-material classification M4's tier
    view groups by and M5's terminator table reuses. Types the mirror
    lacks (or with no group) key (None, None); the display layer falls
    back to a name-list for the catch-all groups (the reference model's
    lesson: 'Commodities' and 'Mineral' hide members that belong
    elsewhere)."""
    if not type_ids:
        return {}
    rows = (
        await db.execute(
            text(
                """
                SELECT t.typeID, c.categoryName, g.groupName
                FROM sde_invTypes t
                LEFT JOIN sde_invGroups g ON g.groupID = t.groupID
                LEFT JOIN sde_invCategories c ON c.categoryID = g.categoryID
                WHERE t.typeID IN :type_ids
                """
            ).bindparams(bindparam("type_ids", expanding=True)),
            {"type_ids": list(type_ids)},
        )
    ).all()
    categories = {type_id: (None, None) for type_id in type_ids}
    for type_id, category_name, group_name in rows:
        categories[type_id] = (category_name, group_name)
    return categories


# ---------------------------------------------------------------------------
# Chain read helpers (M5) — set-at-a-time reads for the recursive resolver.
# The single-commodity reads above run several queries per type, fine for
# one blueprint and unacceptable for an eighty-buildable chain; these batch
# the same data (same producer rule, same name merge) so a whole chain
# resolves in a handful of queries. app/planner.py's resolver and
# orchestrators consume them; interpretation stays there.
# ---------------------------------------------------------------------------


async def recipe_headers(
    db: AsyncSession, type_ids: list[int]
) -> dict[int, RecipeHeader]:
    """Producer facts for a set of product types in one read: the
    prefer-published producer (the rule every catalog read uses),
    products per run, max production limit, and the producing + copy
    durations. Types with no producing activity-1/11 row key nothing —
    absence is the chain walk's terminator signal, never an error."""
    if not type_ids:
        return {}
    rows = (
        await db.execute(
            text(
                f"""
                WITH prod AS (
                    {_PRODUCER_CTE} AND p.productTypeID IN :type_ids
                )
                SELECT prod.product_id,
                       prod.bp_type_id,
                       coalesce(bpName.typeName, bpUni.name,
                                '#' || prod.bp_type_id) AS blueprint_name,
                       prod.activity_id,
                       prod.products_per_run,
                       ib.maxProductionLimit,
                       act.time AS duration,
                       cpy.time AS copy_duration
                FROM prod
                LEFT JOIN sde_invTypes bpName ON bpName.typeID = prod.bp_type_id
                LEFT JOIN universe_types bpUni ON bpUni.type_id = prod.bp_type_id
                LEFT JOIN sde_industryBlueprints ib
                       ON ib.typeID = prod.bp_type_id
                LEFT JOIN sde_industryActivity act
                       ON act.typeID = prod.bp_type_id
                      AND act.activityID = prod.activity_id
                LEFT JOIN sde_industryActivity cpy
                       ON cpy.typeID = prod.bp_type_id
                      AND cpy.activityID = 5
                WHERE prod.rn = 1
                """
            ).bindparams(bindparam("type_ids", expanding=True)),
            {"type_ids": list(type_ids)},
        )
    ).all()
    return {
        product_id: RecipeHeader(
            type_id=product_id,
            blueprint_type_id=bp_type_id,
            blueprint_name=blueprint_name,
            activity_id=activity_id,
            products_per_run=products_per_run,
            max_production_limit=max_limit,
            duration_seconds=duration,
            copy_duration_seconds=copy_duration,
        )
        for (product_id, bp_type_id, blueprint_name, activity_id,
             products_per_run, max_limit, duration, copy_duration) in rows
    }


async def activity_materials(
    db: AsyncSession, bp_type_ids: list[int]
) -> dict[tuple[int, int], list[ChainMaterial]]:
    """Per-run material lists for a set of blueprints' walk activities
    (1 and 11), keyed (blueprint_type_id, activity_id) — the resolver
    re-keys by product through the header. Ordered quantity-first like
    the single-commodity read."""
    if not bp_type_ids:
        return {}
    rows = (
        await db.execute(
            text(
                """
                SELECT m.typeID, m.activityID, m.materialTypeID, m.quantity
                FROM sde_industryActivityMaterials m
                WHERE m.typeID IN :bp_type_ids AND m.activityID IN (1, 11)
                ORDER BY m.typeID, m.activityID,
                         m.quantity DESC, m.materialTypeID
                """
            ).bindparams(bindparam("bp_type_ids", expanding=True)),
            {"bp_type_ids": list(bp_type_ids)},
        )
    ).all()
    materials: dict[tuple[int, int], list[ChainMaterial]] = {}
    for bp_type_id, activity_id, material_type_id, quantity in rows:
        materials.setdefault((bp_type_id, activity_id), []).append(
            ChainMaterial(type_id=material_type_id, quantity_per_run=quantity)
        )
    return materials


async def activity_skills(
    db: AsyncSession, bp_type_ids: list[int]
) -> dict[tuple[int, int], list[RecipeSkill]]:
    """DISTINCT-deduped required skills per (blueprint, activity) for the
    walk activities — the chain's per-node skill gates. Names follow the
    merge rule (SDE first, universe fallback)."""
    if not bp_type_ids:
        return {}
    rows = (
        await db.execute(
            text(
                """
                SELECT DISTINCT s.typeID, s.activityID, s.skillID,
                       coalesce(st.typeName, us.name,
                                '#' || s.skillID) AS name,
                       s.level
                FROM sde_industryActivitySkills s
                LEFT JOIN sde_invTypes st ON st.typeID = s.skillID
                LEFT JOIN universe_types us ON us.type_id = s.skillID
                WHERE s.typeID IN :bp_type_ids AND s.activityID IN (1, 11)
                ORDER BY s.typeID, s.activityID, s.level DESC, name, s.skillID
                """
            ).bindparams(bindparam("bp_type_ids", expanding=True)),
            {"bp_type_ids": list(bp_type_ids)},
        )
    ).all()
    skills: dict[tuple[int, int], list[RecipeSkill]] = {}
    for bp_type_id, activity_id, skill_id, name, level in rows:
        skills.setdefault((bp_type_id, activity_id), []).append(
            RecipeSkill(skill_id=skill_id, name=name, level=level)
        )
    return skills


async def type_names(db: AsyncSession, type_ids: list[int]) -> dict[int, str]:
    """Names for an arbitrary id set (terminators included) under the
    merge rule: the SDE name authoritative, universe_types only for ids
    the dump lacks, '#<id>' when neither holds."""
    if not type_ids:
        return {}
    sde = dict(
        (
            await db.execute(
                text(
                    "SELECT typeID, typeName FROM sde_invTypes"
                    " WHERE typeID IN :type_ids"
                ).bindparams(bindparam("type_ids", expanding=True)),
                {"type_ids": list(type_ids)},
            )
        ).all()
    )
    universe: dict[int, str] = {}
    missing = [type_id for type_id in type_ids if sde.get(type_id) is None]
    if missing:
        universe = dict(
            (
                await db.execute(
                    text(
                        "SELECT type_id, name FROM universe_types"
                        " WHERE type_id IN :type_ids"
                    ).bindparams(bindparam("type_ids", expanding=True)),
                    {"type_ids": missing},
                )
            ).all()
        )
    names: dict[int, str] = {}
    for type_id in type_ids:
        name = sde.get(type_id)
        if name is None:
            name = universe.get(type_id)
        names[type_id] = name if name is not None else f"#{type_id}"
    return names


async def pool_on_hand(
    db: AsyncSession,
    type_ids: list[int],
    *,
    corporation_id: int | None,
    personal_character_ids: list[int] | None = None,
) -> dict[int, int]:
    """On-hand quantities per type over the plan's inventory pool. The
    default measures the main corporation's office hangars ONLY — the
    shared pool corporate plans draw from; personal hangars opt in
    per character via `personal_character_ids` (the owner's
    per-character call, 2026-11-24: participants — out-of-corp ones
    especially — may be job-allocation positions rather than material
    sources, so whose hangar counts is an individual choice, never a
    pool-wide switch). The caller owns the intersect with the
    participant pool; this read counts exactly the ids it is handed.
    Corporation assets outside offices never count. Unheld types key
    zero, not absence."""
    if not type_ids:
        return {}
    on_hand = {type_id: 0 for type_id in type_ids}
    if personal_character_ids:
        rows = (
            await db.execute(
                text(
                    """
                    SELECT a.type_id, sum(a.quantity)
                    FROM assets a
                    WHERE a.owner_type = :char_kind
                      AND a.owner_id IN :personal_ids
                      AND a.type_id IN :type_ids
                    GROUP BY a.type_id
                    """
                ).bindparams(
                    bindparam("personal_ids", expanding=True),
                    bindparam("type_ids", expanding=True),
                ),
                {
                    "char_kind": OWNER_CHARACTER,
                    "personal_ids": list(personal_character_ids),
                    "type_ids": list(type_ids),
                },
            )
        ).all()
        for type_id, quantity in rows:
            on_hand[type_id] += quantity
    if corporation_id is not None:
        # Office hangars only: contents share the office marker's parent
        # (the corporation_offices pattern); the marker itself is not
        # inventory and never counts.
        rows = (
            await db.execute(
                text(
                    """
                    SELECT a.type_id, sum(a.quantity)
                    FROM assets a
                    WHERE a.owner_type = :corp_kind
                      AND a.owner_id = :corporation_id
                      AND a.type_id IN :type_ids
                      AND a.type_id != :office_type
                      AND a.parent_location_id IN (
                          SELECT parent_location_id FROM assets
                           WHERE owner_type = :corp_kind
                             AND owner_id = :corporation_id
                             AND location_flag IN :office_flags
                      )
                    GROUP BY a.type_id
                    """
                ).bindparams(
                    bindparam("type_ids", expanding=True),
                    bindparam("office_flags", expanding=True),
                ),
                {
                    "corp_kind": OWNER_CORPORATION,
                    "corporation_id": corporation_id,
                    "type_ids": list(type_ids),
                    "office_type": OFFICE_TYPE_ID,
                    "office_flags": list(OFFICE_FLAGS),
                },
            )
        ).all()
        for type_id, quantity in rows:
            on_hand[type_id] += quantity
    return on_hand


async def material_source_stock(
    db: AsyncSession,
    type_ids: list[int],
    *,
    corporation_id: int | None,
    participant_ids: list[int],
) -> list[MaterialSource]:
    """Per-source on-hand stock over the plan's material sources: one
    MaterialSource per corp office hangar, per participant personal
    hangar at each location, and per station container inside a corp
    office hangar. Sources holding none of the measured types are
    omitted (the selector shows only relevant locations — a roster
    spans dozens). Buckets are DISJOINT: an office's quantity is its
    loose hangar content (container contents belong to their container
    source, so office + containers never double-count), and personal
    containers roll into their location's hangar source. The caller
    applies selection (sum a subset, or all when no selection exists);
    this read never filters."""
    if not type_ids:
        return []
    sources: list[MaterialSource] = []
    if corporation_id is not None:
        # Office parents (the structures with a rented office), then
        # everything under them grouped per office, minus the containers
        # (computed in Python — no SQL NOT IN edge cases).
        office_rows = (
            await db.execute(
                text(
                    """
                    SELECT DISTINCT parent_location_id FROM assets
                    WHERE owner_type = :corp_kind
                      AND owner_id = :corporation_id
                      AND location_flag IN :office_flags
                    """
                ).bindparams(bindparam("office_flags", expanding=True)),
                {
                    "corp_kind": OWNER_CORPORATION,
                    "corporation_id": corporation_id,
                    "office_flags": list(OFFICE_FLAGS),
                },
            )
        ).all()
        office_parents = [row[0] for row in office_rows]
        per_office: dict[int, dict[int, int]] = {}
        if office_parents:
            rows = (
                await db.execute(
                    text(
                        """
                        SELECT a.parent_location_id, a.type_id, sum(a.quantity)
                        FROM assets a
                        WHERE a.owner_type = :corp_kind
                          AND a.owner_id = :corporation_id
                          AND a.type_id IN :type_ids
                          AND a.type_id != :office_type
                          AND a.parent_location_id IN :office_parents
                        GROUP BY a.parent_location_id, a.type_id
                        """
                    ).bindparams(
                        bindparam("type_ids", expanding=True),
                        bindparam("office_parents", expanding=True),
                    ),
                    {
                        "corp_kind": OWNER_CORPORATION,
                        "corporation_id": corporation_id,
                        "type_ids": list(type_ids),
                        "office_type": OFFICE_TYPE_ID,
                        "office_parents": office_parents,
                    },
                )
            ).all()
            for parent, type_id, quantity in rows:
                per_office.setdefault(parent, {})[type_id] = quantity
        # Containers: corp asset rows inside office hangars that other
        # corp assets report as their location_id (the marker itself is
        # the office, never a container). No offices means no corp
        # containers either — the parent filter is what scopes them to
        # the hangars.
        per_container: dict[int, dict[int, int]] = {}
        container_parent: dict[int, int] = {}
        container_rows: list[tuple[int, int, int]] = []
        if office_parents:
            container_rows = (
                await db.execute(
                    text(
                        """
                        SELECT DISTINCT c.item_id, c.parent_location_id,
                                        c.type_id
                        FROM assets c
                        WHERE c.owner_type = :corp_kind
                          AND c.owner_id = :corporation_id
                          AND c.parent_location_id IN :office_parents
                          AND c.location_flag NOT IN :office_flags
                          AND c.item_id IN (
                              SELECT location_id FROM assets
                               WHERE owner_type = :corp_kind
                                 AND owner_id = :corporation_id
                                 AND location_type = 'item'
                          )
                        """
                    ).bindparams(
                        bindparam("office_parents", expanding=True),
                        bindparam("office_flags", expanding=True),
                    ),
                    {
                        "corp_kind": OWNER_CORPORATION,
                        "corporation_id": corporation_id,
                        "office_parents": office_parents,
                        "office_flags": list(OFFICE_FLAGS),
                    },
                )
            ).all()
        if container_rows:
            container_ids = [row[0] for row in container_rows]
            container_parent = {row[0]: row[1] for row in container_rows}
            container_types = {row[0]: row[2] for row in container_rows}
            rows = (
                await db.execute(
                    text(
                        """
                        SELECT a.location_id, a.type_id, sum(a.quantity)
                        FROM assets a
                        WHERE a.owner_type = :corp_kind
                          AND a.owner_id = :corporation_id
                          AND a.type_id IN :type_ids
                          AND a.location_id IN :container_ids
                        GROUP BY a.location_id, a.type_id
                        """
                    ).bindparams(
                        bindparam("type_ids", expanding=True),
                        bindparam("container_ids", expanding=True),
                    ),
                    {
                        "corp_kind": OWNER_CORPORATION,
                        "corporation_id": corporation_id,
                        "type_ids": list(type_ids),
                        "container_ids": container_ids,
                    },
                )
            ).all()
            for item_id, type_id, quantity in rows:
                per_container.setdefault(item_id, {})[type_id] = quantity
        for parent, quantities in per_office.items():
            # Loose office stock: the office's total minus its
            # containers' contents (disjoint buckets — see docstring).
            loose = dict(quantities)
            for item_id, held in per_container.items():
                if container_parent.get(item_id) == parent:
                    for type_id, quantity in held.items():
                        loose[type_id] = loose.get(type_id, 0) - quantity
            loose = {t: q for t, q in loose.items() if q > 0}
            if loose:
                sources.append(
                    MaterialSource(
                        kind="office",
                        ref=f"office:{parent}",
                        character_id=None,
                        location_id=parent,
                        container_item_id=None,
                        quantities=loose,
                    )
                )
        for item_id, quantities in per_container.items():
            if quantities:
                sources.append(
                    MaterialSource(
                        kind="container",
                        ref=f"container:{item_id}",
                        character_id=None,
                        location_id=container_parent.get(item_id),
                        container_item_id=item_id,
                        container_type_id=container_types.get(item_id),
                        quantities=quantities,
                    )
                )
    if participant_ids:
        rows = (
            await db.execute(
                text(
                    """
                    SELECT a.owner_id, a.parent_location_id, a.type_id,
                           sum(a.quantity)
                    FROM assets a
                    WHERE a.owner_type = :char_kind
                      AND a.owner_id IN :participant_ids
                      AND a.type_id IN :type_ids
                    GROUP BY a.owner_id, a.parent_location_id, a.type_id
                    """
                ).bindparams(
                    bindparam("participant_ids", expanding=True),
                    bindparam("type_ids", expanding=True),
                ),
                {
                    "char_kind": OWNER_CHARACTER,
                    "participant_ids": list(participant_ids),
                    "type_ids": list(type_ids),
                },
            )
        ).all()
        per_hangar: dict[tuple[int, int], dict[int, int]] = {}
        for owner, parent, type_id, quantity in rows:
            per_hangar.setdefault((owner, parent), {})[type_id] = quantity
        for (owner, parent), quantities in per_hangar.items():
            sources.append(
                MaterialSource(
                    kind="hangar",
                    ref=f"hangar:{owner}:{parent}",
                    character_id=owner,
                    location_id=parent,
                    container_item_id=None,
                    quantities=quantities,
                )
            )
    return sources
