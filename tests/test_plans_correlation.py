"""Industry-job correlation tests (M6 PR 6): the heuristic matcher
that attaches synced industry jobs to plan nodes — blueprint type plus
the ESI→SDE activity reconciliation as the keys, the pinned facility's
sighting location as a filter (only when the structure has one), plan
creation as the recency floor, and the global one-claim rule across
concurrent plans. The matcher itself is pure; these tests drive it
through the DB pass (refresh_job_claims) over the miniature golden
chain so the pinned facilities and node rows are real exports, plus
one hand-built-refs test for the within-plan phase preference."""

from datetime import timedelta

from sqlalchemy import select

from app.db import utc_now
from app.models import (
    BuildPlan,
    BuildPlanJob,
    BuildPlanNode,
    IndustryJob,
    Structure,
)
from app.planner import chain_plan
from app.plans import (
    PlanNodeRef,
    PlanRef,
    correlate_jobs,
    refresh_job_claims,
    snapshot_plan,
)
from tests.test_planner_chain import (  # noqa: F401  (fixture)
    CARBIDE,
    FUEL,
    TYPHOON,
    _facilities,
    chain_db,
)
from tests.test_planner_plan import MAIN, planner_db  # noqa: F401  (fixture)

CORP = 98000001
FUEL_BP = 4101  # the fuel block's manufacturing blueprint
REACTION_BP = 46207  # the carbide formula (SDE activity 11)

# Unique job ids per call — the industry_jobs key is owner × job_id.
_job_seq = iter(range(1, 100_000))


def _job(**fields):
    """A synced corp industry job one hour from now by default — every
    matcher key overridable."""
    defaults = dict(
        owner_type="corporation",
        owner_id=CORP,
        job_id=next(_job_seq),
        installer_id=MAIN,
        activity_id=1,
        blueprint_type_id=FUEL_BP,
        runs=1,
        successful_runs=None,
        status="active",
        start_date=utc_now() + timedelta(hours=1),
        end_date=None,
        completed_date=None,
        station_id=None,
    )
    defaults.update(fields)
    return IndustryJob(**defaults)


async def _export(db, units=10) -> BuildPlan:
    """A real exported plan over the golden chain — the route handler's
    chain_plan + snapshot_plan pair, minus the HTTP layer."""
    facilities = await _facilities(db)
    resolved = await chain_plan(
        db, target_type_id=TYPHOON, units=units, facilities=facilities
    )
    plan = await snapshot_plan(
        db,
        resolved=resolved,
        facilities=facilities,
        name=f"Correlation ×{units}",
        source_query="",
        sources=None,
    )
    await db.commit()
    return plan


async def _node(db, plan_id, type_id) -> BuildPlanNode:
    row = (
        await db.execute(
            select(BuildPlanNode).where(
                BuildPlanNode.plan_id == plan_id,
                BuildPlanNode.type_id == type_id,
            )
        )
    ).scalar_one()
    return row


async def _claim_rows(db) -> list[BuildPlanJob]:
    return (
        (
            await db.execute(
                select(BuildPlanJob).order_by(
                    BuildPlanJob.plan_id, BuildPlanJob.node_id, BuildPlanJob.job_id
                )
            )
        )
        .scalars()
        .all()
    )


async def test_blueprint_and_activity_claim_the_node(chain_db):  # noqa: F811
    """A job whose blueprint and (reconciled) activity equal a node's
    claims it — the strongest-key happy path."""
    plan = await _export(chain_db)
    job = _job()
    chain_db.add(job)

    claims = await refresh_job_claims(chain_db)
    await chain_db.commit()

    fuel = await _node(chain_db, plan.id, FUEL)
    assert [(c.plan_id, c.node_id, c.job_id) for c in claims] == [
        (plan.id, fuel.id, job.job_id)
    ]
    rows = await _claim_rows(chain_db)
    assert len(rows) == 1
    assert rows[0].owner_type == "corporation"
    assert rows[0].owner_id == CORP
    assert rows[0].job_id == job.job_id


async def test_reaction_activity_nine_reconciles_to_eleven(chain_db):  # noqa: F811
    """ESI reports reaction jobs under activity 9 while the SDE (and so
    the plan nodes) carry 11 — both report spellings claim the reaction
    node; a manufacturing-activity job on the same formula does not."""
    plan = await _export(chain_db)
    esi_reaction = _job(activity_id=9, blueprint_type_id=REACTION_BP)
    sde_spelling = _job(activity_id=11, blueprint_type_id=REACTION_BP)
    wrong_activity = _job(activity_id=1, blueprint_type_id=REACTION_BP)
    chain_db.add_all([esi_reaction, sde_spelling, wrong_activity])

    await refresh_job_claims(chain_db)
    await chain_db.commit()

    carbide = await _node(chain_db, plan.id, CARBIDE)
    rows = await _claim_rows(chain_db)
    assert {row.job_id for row in rows} == {esi_reaction.job_id, sde_spelling.job_id}
    assert all(row.node_id == carbide.id for row in rows)


async def test_location_filters_only_with_a_known_location(chain_db):  # noqa: F811
    """The location filter applies only when the node's pinned facility
    resolved to a sighting location: jobs elsewhere on that node miss,
    while a hand-entered facility (no location) matches loosely — the
    documented failure mode."""
    plan = await _export(chain_db)
    azbel = (
        await chain_db.execute(
            select(Structure).where(Structure.structure_type == "azbel")
        )
    ).scalar_one()
    azbel.location_id = 4_000_000_001
    at_facility = _job(station_id=4_000_000_001)
    elsewhere = _job(station_id=4_000_000_002)
    # The reaction facility (Tatara) is hand-entered: any location.
    loose = _job(
        activity_id=9, blueprint_type_id=REACTION_BP, station_id=999_999
    )
    chain_db.add_all([at_facility, elsewhere, loose])

    await refresh_job_claims(chain_db)
    await chain_db.commit()

    fuel = await _node(chain_db, plan.id, FUEL)
    carbide = await _node(chain_db, plan.id, CARBIDE)
    rows = await _claim_rows(chain_db)
    assert {(row.node_id, row.job_id) for row in rows} == {
        (fuel.id, at_facility.job_id),
        (carbide.id, loose.job_id),
    }


async def test_pre_export_installs_never_claim(chain_db):  # noqa: F811
    """Recency floor: a job started before the plan was exported belongs
    to a previous effort; one started at the exact creation moment
    claims (the floor is inclusive)."""
    plan = await _export(chain_db)
    before = _job(start_date=plan.created_at - timedelta(seconds=1))
    at_floor = _job(start_date=plan.created_at)
    chain_db.add_all([before, at_floor])

    await refresh_job_claims(chain_db)
    await chain_db.commit()

    rows = await _claim_rows(chain_db)
    assert [row.job_id for row in rows] == [at_floor.job_id]


async def test_terminal_job_statuses_never_claim(chain_db):  # noqa: F811
    """cancelled/reverted jobs are excluded; the live spellings
    (active, paused, ready, delivered) all carry claims."""
    await _export(chain_db)
    jobs = {
        status: _job(status=status)
        for status in (
            "active", "paused", "ready", "delivered", "cancelled", "reverted",
        )
    }
    chain_db.add_all(jobs.values())

    await refresh_job_claims(chain_db)
    await chain_db.commit()

    live = {
        jobs[status].job_id for status in ("active", "paused", "ready", "delivered")
    }
    rows = await _claim_rows(chain_db)
    assert {row.job_id for row in rows} == live


async def test_one_claim_per_job_oldest_plan_wins(chain_db):  # noqa: F811
    """The global one-claim rule: a job matching nodes in two concurrent
    plans claims into the older one only — the concurrent-plan
    false-positive guard."""
    first = await _export(chain_db)
    second = await _export(chain_db)
    # Make the ordering explicit (a same-instant pair would fall to ids).
    first.created_at = first.created_at - timedelta(days=1)
    job = _job()
    chain_db.add(job)

    await refresh_job_claims(chain_db)
    await chain_db.commit()

    rows = await _claim_rows(chain_db)
    assert len(rows) == 1
    assert rows[0].plan_id == first.id != second.id
    assert rows[0].job_id == job.job_id


async def test_terminal_plans_do_not_claim(chain_db):  # noqa: F811
    """Abandoned (and complete) plans leave the matching pool — their
    nodes' claims are not written, so a live sibling takes the job."""
    abandoned = await _export(chain_db)
    live = await _export(chain_db)
    abandoned.status = "abandoned"
    job = _job()
    chain_db.add(job)

    await refresh_job_claims(chain_db)
    await chain_db.commit()

    rows = await _claim_rows(chain_db)
    assert len(rows) == 1
    assert rows[0].plan_id == live.id


async def test_claims_rewrite_wholesale(chain_db):  # noqa: F811
    """The write path replaces build_plan_jobs wholesale: stale rows
    from a previous pass (a job that no longer matches, a claim whose
    job went terminal) are gone after the refresh."""
    plan = await _export(chain_db)
    fuel = await _node(chain_db, plan.id, FUEL)
    cancelled = _job(status="cancelled")
    live = _job()
    chain_db.add_all([cancelled, live])
    chain_db.add_all(
        [
            # A claim whose job went terminal since the last pass…
            BuildPlanJob(
                plan_id=plan.id,
                node_id=fuel.id,
                owner_type="corporation",
                owner_id=CORP,
                job_id=cancelled.job_id,
            ),
            # …and one whose job key no longer matches anything.
            BuildPlanJob(
                plan_id=plan.id,
                node_id=fuel.id,
                owner_type="corporation",
                owner_id=CORP,
                job_id=987_654,
            ),
        ]
    )

    await refresh_job_claims(chain_db)
    await chain_db.commit()

    rows = await _claim_rows(chain_db)
    assert [row.job_id for row in rows] == [live.job_id]


def test_within_plan_a_job_claims_the_earliest_phase():
    """Recurring-commodity shape (the Charon chain's rule): the same
    blueprint at two phases of one plan — the earlier phase claims
    first (build order), the later occurrence waits for its own jobs.
    Pure: hand-built refs, no DB."""
    plan = PlanRef(
        plan_id=1,
        created_at=utc_now(),
        nodes=(
            PlanNodeRef(
                node_id=11, phase=0, blueprint_type_id=500,
                activity_id=1, facility_location_id=None,
            ),
            PlanNodeRef(
                node_id=12, phase=2, blueprint_type_id=500,
                activity_id=1, facility_location_id=None,
            ),
        ),
    )
    job = _job(blueprint_type_id=500)
    claims = correlate_jobs([plan], [job])
    assert [(claim.node_id, claim.job_id) for claim in claims] == [
        (11, job.job_id)
    ]
