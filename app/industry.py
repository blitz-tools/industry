"""Industry data view layer: pure DB reads for the corporation
blueprints and jobs pages. The planner (M4+) will build on these joins —
blueprints carry ME/TE/runs the planner multiplies against, jobs carry
the activity ids that join the SDE (M2).
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import String, and_, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from .esi.assets import OWNER_CORPORATION
from .models import (
    Asset,
    Blueprint,
    Character,
    IndustryJob,
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

    @property
    def status_class(self) -> str:
        return JOB_STATUS_CLASSES.get(self.status, "warn")


async def corporation_blueprints(
    db: AsyncSession, corporation_id: int, *, page: int, page_size: int
) -> tuple[list[BlueprintRow], int, int]:
    """One page of the corporation's blueprints, name-ordered. Location
    names come from the universe cache (asset syncs populate it); unknown
    locations read as None and the template falls back to the raw id."""
    conditions = [
        Blueprint.owner_type == OWNER_CORPORATION,
        Blueprint.owner_id == corporation_id,
    ]
    total = (
        await db.execute(select(func.count()).select_from(Blueprint).where(*conditions))
    ).scalar_one()
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
    rows_raw = (
        await db.execute(
            select(
                Blueprint.item_id,
                Blueprint.type_id,
                UniverseType.name,
                Blueprint.material_efficiency,
                Blueprint.time_efficiency,
                Blueprint.runs,
                location_name,
                Blueprint.location_flag,
            )
            .outerjoin(UniverseType, UniverseType.type_id == Blueprint.type_id)
            .outerjoin(
                UniverseLocation, UniverseLocation.location_id == Blueprint.location_id
            )
            .outerjoin(
                Asset,
                and_(
                    Asset.owner_type == OWNER_CORPORATION,
                    Asset.owner_id == corporation_id,
                    Asset.item_id == Blueprint.location_id,
                ),
            )
            .outerjoin(
                parent_location,
                parent_location.location_id == Asset.parent_location_id,
            )
            .where(*conditions)
            .order_by(type_name, Blueprint.item_id)
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
    ).all()
    rows = []
    for (item_id, type_id, name, me, te, runs, loc_name, flag) in rows_raw:
        rows.append(
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
            )
        )
    return rows, total, page


async def corporation_jobs(
    db: AsyncSession,
    corporation_id: int,
    *,
    include_completed: bool,
    page: int,
    page_size: int,
) -> tuple[list[JobRow], int, int]:
    """One page of the corporation's industry jobs, newest first. Installers
    resolve through the tracked characters (the common case — corp members);
    anyone else reads as their raw character id."""
    conditions = [
        IndustryJob.owner_type == OWNER_CORPORATION,
        IndustryJob.owner_id == corporation_id,
    ]
    if not include_completed:
        conditions.append(IndustryJob.status.in_(ACTIVE_JOB_STATUSES))
    total = (
        await db.execute(
            select(func.count()).select_from(IndustryJob).where(*conditions)
        )
    ).scalar_one()
    pages = max(1, -(-total // page_size))
    page = min(max(1, page), pages)

    rows_raw = (
        await db.execute(
            select(
                IndustryJob.job_id,
                IndustryJob.activity_id,
                IndustryJob.blueprint_type_id,
                UniverseType.name,
                Character.name,
                IndustryJob.installer_id,
                IndustryJob.runs,
                IndustryJob.successful_runs,
                IndustryJob.status,
                IndustryJob.start_date,
                IndustryJob.end_date,
            )
            .outerjoin(
                UniverseType, UniverseType.type_id == IndustryJob.blueprint_type_id
            )
            .outerjoin(Character, Character.character_id == IndustryJob.installer_id)
            .where(*conditions)
            .order_by(IndustryJob.start_date.desc().nulls_last(), IndustryJob.job_id)
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
        ) in rows_raw
    ]
    return rows, total, page
