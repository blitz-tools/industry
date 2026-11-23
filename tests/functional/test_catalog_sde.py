"""Functional proof of the catalog query layer against a live SDE
mirror — the CI counterpart of the M2 validation recorded in
MILESTONES.md.

Gated on ``SDE_PROOF_DB`` pointing at a SQLite database holding a
loaded mirror (plus the app tables for the owned-overlay joins; the
fixture creates them only when missing, so pointing at the dev
deployment's industry.db never issues DDL). Without the variable the
module skips, keeping plain ``pytest`` runs hermetic.

Two evidence blocks, mirroring the recorded proof:

1. **Golden-source parity** — ``commodity_recipe`` checked against
   ``reference/chain_expand.py`` (the executable spec behind the chain
   documents) for the ten chain anchors: producer choice, products per
   run, every material row, duration, and deduped skills.
2. **Edge-case invariants through the real functions** — census
   membership parity (the catalog size is whatever the current dump
   holds; both sides are computed at run time, nothing hard-coded),
   prefer-published producers on every multi-producer product,
   invention-only and raw types rejected, name-merge and search
   behavior, and dump-state canaries (duplicate rows) whose failure
   means the recipe read needs a new interpretation rule.

The catalog-proof workflow runs this against a freshly downloaded
fuzzwork dump; pointing SDE_PROOF_DB at the dev deployment's database
runs the same proof against live data.
"""

import importlib.util
import os
import sqlite3
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import Base
from app.industry import commodity_recipe, search_catalog
from app.models import Blueprint  # noqa: F401  (register models)

PROOF_DB = os.environ.get("SDE_PROOF_DB")

pytestmark = pytest.mark.skipif(
    not PROOF_DB or not Path(PROOF_DB).is_file(),
    reason="SDE_PROOF_DB not set to a database holding a loaded mirror",
)

REPO_ROOT = Path(__file__).resolve().parents[2]

# The executable spec, loaded from its non-package home in reference/.
_spec = importlib.util.spec_from_file_location(
    "chain_expand", REPO_ROOT / "reference" / "chain_expand.py"
)
chain_expand = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(chain_expand)

# The ten chain anchors (name, product type id) — the acceptance suite.
# Golden producers come from chain_expand at run time, never baked in.
ANCHORS = [
    ("Typhoon", 644),
    ("Charon", 20185),
    ("Panther", 22440),
    ("Jackdaw", 34828),
    ("Large Trimark Armor Pump II", 26302),
    ("Scourge Rage Heavy Assault Missile", 2679),
    ("Strong Crash Booster", 10152),
    ("Hel", 22852),
    ("Typhoon Fleet Issue", 32311),
    ("Ragnarok", 23773),
]


@pytest.fixture
def sde() -> sqlite3.Connection:
    """Synchronous read-only connection for golden-source and SQL-side
    reads of the same database the async session sees."""
    return sqlite3.connect(f"file:{PROOF_DB}?mode=ro", uri=True)


@pytest_asyncio.fixture
async def db():
    """Async session over the proof database. The catalog search's
    owned-count subqueries reference the app tables, so they are created
    when missing (a fresh mirror-only database) — against a deployment
    database they already exist and no DDL runs."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{PROOF_DB}")
    async with engine.connect() as conn:
        if not await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).has_table("blueprints")
        ):
            await conn.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session
    await engine.dispose()


# --- 1. Golden-source parity: recipe vs chain_expand ----------------------


@pytest.mark.parametrize(("name", "type_id"), ANCHORS)
async def test_anchor_recipe_matches_golden_source(db, sde, name, type_id):
    """Producer, products/run, materials, and duration read identically
    through the app's query layer and the reference implementation."""
    bp, activity, per_run = chain_expand.producers(sde, type_id)[0]
    golden_materials = sorted(
        (material_id, quantity)
        for material_id, quantity in chain_expand.inputs(sde, bp, activity)
    )
    golden_time = sde.execute(
        "SELECT time FROM sde_industryActivity WHERE typeID=? AND activityID=?",
        (bp, activity),
    ).fetchone()

    recipe = await commodity_recipe(db, type_id)
    assert recipe is not None, f"{name} is not a catalog commodity"
    assert recipe.blueprint_type_id == bp
    assert recipe.products_per_run == per_run
    assert recipe.activity_id == activity
    assert sorted(
        (m.type_id, m.quantity_per_run) for m in recipe.materials
    ) == golden_materials
    assert recipe.duration_seconds == (
        golden_time[0] if golden_time else None
    )


@pytest.mark.parametrize(("name", "type_id"), ANCHORS)
async def test_anchor_skills_are_deduped_dump_rows(db, sde, name, type_id):
    """The recipe's skills are exactly the dump's DISTINCT skill rows
    for the activity — the verbatim mirror carries duplicates."""
    bp, activity, _ = chain_expand.producers(sde, type_id)[0]
    golden_skills = sorted(
        sde.execute(
            "SELECT DISTINCT skillID, level FROM sde_industryActivitySkills"
            " WHERE typeID=? AND activityID=?",
            (bp, activity),
        ).fetchall()
    )
    recipe = await commodity_recipe(db, type_id)
    assert sorted((s.skill_id, s.level) for s in recipe.skills) == golden_skills


# --- 2. Edge-case invariants through the real functions -------------------


async def test_search_enumerates_full_census_membership(db, sde):
    """Empty-pattern search enumerates every catalog member (products of
    activities 1 and 11) — a NULL name must never silently drop one
    (SQL NULL LIKE excludes it; the #id fallback keeps it enumerable).
    Both counts are computed at run time: the catalog's size is whatever
    the current dump holds."""
    sql_count = sde.execute(
        "SELECT COUNT(DISTINCT productTypeID) FROM sde_industryActivityProducts"
        " WHERE activityID IN (1, 11)"
    ).fetchone()[0]
    entries = await search_catalog(db, "", limit=10_000_000)
    assert len(entries) == sql_count
    assert all(e.type_name for e in entries)


async def test_multi_producer_products_prefer_published_producer(db, sde):
    """Every product with more than one producer row (activities 1 and
    11) resolves to a published producer whenever one exists — the
    dump's unpublished CCP test artifacts must never win by rowid."""
    multi_producers = [
        row[0]
        for row in sde.execute(
            "SELECT productTypeID FROM sde_industryActivityProducts"
            " WHERE activityID IN (1, 11)"
            " GROUP BY productTypeID HAVING COUNT(*) > 1"
            " ORDER BY productTypeID"
        ).fetchall()
    ]
    assert multi_producers, "no multi-producer products in this dump?"
    for type_id in multi_producers:
        has_published = sde.execute(
            "SELECT 1 FROM sde_industryActivityProducts p"
            " JOIN sde_invTypes t ON t.typeID = p.typeID"
            " WHERE p.productTypeID = ? AND p.activityID IN (1, 11)"
            " AND t.published = 1 LIMIT 1",
            (type_id,),
        ).fetchone()
        if not has_published:
            continue  # only unpublished producers exist: fallback applies
        recipe = await commodity_recipe(db, type_id)
        published = sde.execute(
            "SELECT published FROM sde_invTypes WHERE typeID=?",
            (recipe.blueprint_type_id,),
        ).fetchone()[0]
        assert published == 1, (
            f"type {type_id} ({recipe.type_name}): chose unpublished"
            f" {recipe.blueprint_name}"
        )


async def test_invention_only_products_are_not_commodities(db, sde):
    """Types appearing only as activity-8 (invention) products are
    blueprints, never catalog commodities."""
    invention_only = [
        row[0]
        for row in sde.execute(
            "SELECT productTypeID FROM sde_industryActivityProducts"
            " GROUP BY productTypeID"
            " HAVING SUM(activityID != 8) = 0"
            " ORDER BY productTypeID LIMIT 25"
        ).fetchall()
    ]
    assert invention_only, "no invention-only products in this dump?"
    for type_id in invention_only:
        assert await commodity_recipe(db, type_id) is None, type_id


async def test_raw_types_are_not_commodities(db, sde):
    """Types with no producing blueprint anywhere are raw — the recipe
    read rejects them."""
    raw_types = [
        row[0]
        for row in sde.execute(
            "SELECT t.typeID FROM sde_invTypes t"
            " WHERE NOT EXISTS (SELECT 1 FROM sde_industryActivityProducts p"
            " WHERE p.productTypeID = t.typeID)"
            " ORDER BY t.typeID LIMIT 25"
        ).fetchall()
    ]
    assert raw_types, "every type has a producer in this dump?"
    for type_id in raw_types:
        assert await commodity_recipe(db, type_id) is None, type_id


async def test_search_ordering_casing_whitespace_limit(db):
    """Prefix matches sort first; matching is case-insensitive and
    whitespace-tolerant; the limit is respected."""
    entries = await search_catalog(db, "typhoon")
    assert [e.type_name for e in entries] == [
        "Typhoon", "Typhoon Fleet Issue",
    ]
    assert [e.type_id for e in await search_catalog(db, "TYPHOON")] == [
        e.type_id for e in entries
    ]
    assert [e.type_id for e in await search_catalog(db, "  typhoon  ")] == [
        e.type_id for e in entries
    ]
    assert len(await search_catalog(db, "ty", limit=3)) == 3


async def test_name_merge_prefers_sde_names(db, sde):
    """Where both name sources hold a type, the SDE name displays —
    stale universe rows (e.g. a trailing space) must not leak."""
    (typhoon,) = [
        e for e in await search_catalog(db, "typhoon") if e.type_id == 644
    ]
    assert typhoon.type_name == "Typhoon"
    differing = sde.execute(
        "SELECT u.type_id FROM universe_types u JOIN sde_invTypes t"
        " ON t.typeID = u.type_id WHERE u.name != t.typeName"
    ).fetchall()
    if differing:  # a deployment database; a fresh mirror has none
        for (type_id,) in differing:
            sde_name = sde.execute(
                "SELECT typeName FROM sde_invTypes WHERE typeID=?",
                (type_id,),
            ).fetchone()[0]
            recipe = await commodity_recipe(db, type_id)
            if recipe is not None:
                assert recipe.type_name == sde_name, type_id


async def test_owned_overlay_invariants(db, sde):
    """With an empty inventory the overlay reads empty; against a
    deployment database, owned_only is a subset of the full enumeration
    and every owned hit carries a positive owned count."""
    inventory = sde.execute("SELECT count(*) FROM blueprints").fetchone()[0]
    if inventory == 0:
        entries = await search_catalog(db, "typhoon")
        assert all(e.owned_count == 0 for e in entries)
        recipe = await commodity_recipe(db, 644)
        assert recipe is not None and recipe.owned == []
        return
    # Untruncated pages: the subset invariant only holds against a
    # complete enumeration.
    all_ids = {
        e.type_id for e in await search_catalog(db, "typhoon", limit=10_000_000)
    }
    owned = await search_catalog(
        db, "typhoon", limit=10_000_000, owned_only=True
    )
    assert owned, "inventory exists but nothing matches 'typhoon'?"
    assert {e.type_id for e in owned} <= all_ids
    assert all(e.owned_count > 0 for e in owned)


def test_dump_has_no_duplicate_material_rows(sde):
    """Canary: the recipe read does not dedup materials, so duplicate
    material rows in a future dump would double-count inputs. If this
    fails on a new release, add dedup to the recipe read (as the skill
    read already does) and record the rule in MILESTONES.md."""
    duplicates = sde.execute(
        "SELECT COUNT(*) FROM (SELECT typeID, activityID, materialTypeID,"
        " quantity FROM sde_industryActivityMaterials"
        " GROUP BY 1, 2, 3, 4 HAVING COUNT(*) > 1)"
    ).fetchone()[0]
    assert duplicates == 0
