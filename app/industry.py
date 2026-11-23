"""Industry data view layer: pure DB reads for the blueprint, job, and
skill pages (character and corporation). The planner (M4+) builds on
these joins — blueprints carry ME/TE/runs the planner multiplies against,
jobs carry the activity ids that join the SDE, skills feed time math and
slot ceilings.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import String, and_, cast, func, literal, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from .esi.assets import KIND_CHAR_SKILLS, OWNER_CHARACTER, OWNER_CORPORATION
from .models import (
    Asset,
    Blueprint,
    Character,
    DataSync,
    IndustryJob,
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
class CommodityRecipe:
    """Everything the M4 calculator needs for one selected commodity:
    the producing blueprint, its per-run inputs and skills, the activity
    duration, and the owned-blueprint overlay (ME/TE/runs per copy)."""

    type_id: int
    type_name: str
    group_name: str | None
    blueprint_type_id: int
    blueprint_name: str
    activity_id: int
    products_per_run: int
    max_production_limit: int | None
    duration_seconds: int | None  # None: no industryActivity row
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
                WHERE b.type_id = :blueprint_type_id
                ORDER BY owner_name, b.item_id
                """
            ),
            {
                "blueprint_type_id": blueprint_type_id,
                "char_kind": OWNER_CHARACTER,
                "corp_kind": OWNER_CORPORATION,
            },
        )
    ).all()
    return [
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
        for (item_id, type_id, name, me, te, runs, location_name, flag, owner)
        in rows_raw
    ]
