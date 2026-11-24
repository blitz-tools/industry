"""Functional proof of the M5 chain resolver against a live SDE mirror
— the CI counterpart of the M5 validation recorded in MILESTONES.md.

Gated on ``SDE_PROOF_DB`` pointing at a SQLite database holding a
loaded mirror (plus the app tables; the fixture creates them only when
missing, so pointing at the dev deployment's industry.db never issues
DDL). Without the variable the module skips, keeping plain ``pytest``
runs hermetic.

Two evidence blocks:

1. **Ten-anchor chain diff** — the app resolver's BASE walk (no ME or
   facility adjustments — those are pinned hermetically in
   tests/test_planner_chain.py) checked against
   ``reference/chain_expand.py``'s ``--json`` mode (the executable
   spec's structured output): phase count, every phase's rows
   (type, qty, runs, activity), chain-wide raw totals, and the cycle
   cuts. Golden values are recomputed from chain_expand at run time,
   never baked in.
2. **Whole-catalog census parity** — every buildable product resolved
   through the app over one shared catalog: every walk terminates,
   cyclic-type membership matches the reference census's cycle set,
   and every cut-free chain's phase depth matches the reference's
   memoized walk (chains that touch cycles compare membership only —
   the two implementations order cycle entry differently, and the
   anchors pin the cut semantics hermetically).

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
from app.models import Blueprint  # noqa: F401  (register models)
from app.planner import _cyclic_types, build_chain_catalog, resolve_chain

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
    """Synchronous read-only connection for golden-source reads of the
    same database the async session sees."""
    return sqlite3.connect(f"file:{PROOF_DB}?mode=ro", uri=True)


@pytest_asyncio.fixture
async def db():
    """Async session over the proof database (the catalog proof's
    fixture pattern: app tables created only when missing)."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{PROOF_DB}")
    async with engine.connect() as conn:
        if not await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).has_table("blueprints")
        ):
            await conn.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session
    await engine.dispose()


def _app_rows(result):
    """The resolver's output as comparable rows: per ascending phase,
    the sorted (type_id, qty, runs, activity) tuples."""
    return [
        sorted(
            (node.type_id, node.qty, node.runs, node.activity_id)
            for node in phase.nodes
        )
        for phase in result.phases
    ]


def _json_rows(data):
    return [
        sorted(
            (node["type_id"], node["qty"], node["runs"], node["activity"])
            for node in phase["nodes"]
        )
        for phase in data["phases"]
    ]


# --- 1. Ten-anchor chain diff -------------------------------------------------


@pytest.mark.parametrize(("name", "type_id"), ANCHORS)
async def test_anchor_chain_matches_golden_source(db, sde, name, type_id):
    """The app resolver's unadjusted walk is byte-identical to the
    reference implementation's structured output: phases, rows,
    quantities, runs, raw totals, and cycle cuts."""
    catalog = await build_chain_catalog(db, [type_id])
    assert catalog is not None, f"{name} is not a catalog product"
    result = resolve_chain(type_id, 1, catalog)
    golden = chain_expand.chain_json(sde, type_id, 1)

    app_rows = _app_rows(result)
    json_rows = _json_rows(golden)
    assert len(app_rows) == len(json_rows), (
        f"{name}: phase count {len(app_rows)} vs golden {len(json_rows)}"
    )
    for phase_index, (app_phase, golden_phase) in enumerate(
        zip(app_rows, json_rows, strict=True)
    ):
        assert app_phase == golden_phase, (
            f"{name}: phase {phase_index} rows differ"
        )

    app_raw = {row.type_id: row.qty for row in result.raw_totals}
    golden_raw = {row["type_id"]: row["qty"] for row in golden["raw_totals"]}
    assert app_raw == golden_raw, f"{name}: raw totals differ"

    app_cycles = {(c.consumer_type_id, c.material_type_id) for c in result.cycles}
    golden_cycles = {(c["consumer"], c["material"]) for c in golden["cycles"]}
    assert app_cycles == golden_cycles, f"{name}: cycle cuts differ"


@pytest.mark.parametrize(("name", "type_id"), ANCHORS)
async def test_anchor_chain_at_quantity_ten(db, sde, name, type_id):
    """The same diff at ×10 — quantity scaling and the per-phase merge
    arithmetic hold across the anchor set, not just at ×1."""
    catalog = await build_chain_catalog(db, [type_id])
    result = resolve_chain(type_id, 10, catalog)
    golden = chain_expand.chain_json(sde, type_id, 10)
    assert _app_rows(result) == _json_rows(golden)
    assert {row.type_id: row.qty for row in result.raw_totals} == {
        row["type_id"]: row["qty"] for row in golden["raw_totals"]
    }


# --- 2. Whole-catalog census parity ---------------------------------------------


async def test_census_every_product_resolves(db, sde):
    """One shared catalog over every buildable product; every walk
    terminates. Cut-free chains match the reference census's memoized
    depth exactly; chains that touch cycles are checked on membership
    (the reference's path-tracking and the app's level walk order
    cycle entry differently — the anchors pin the cut semantics
    hermetically)."""
    product_ids = [
        row[0]
        for row in sde.execute(
            "SELECT DISTINCT productTypeID FROM sde_industryActivityProducts"
            " WHERE activityID IN (1, 11)"
        )
    ]
    assert len(product_ids) > 5000  # the census membership, at run time

    catalog = await build_chain_catalog(db, product_ids)
    assert catalog is not None
    cyclic = _cyclic_types(catalog)
    reference_depth, back_edges = chain_expand.census(sde)

    # Cyclic membership: the app's SCC classification matches the
    # reference census's back-edge endpoints.
    reference_cyclic = {m for _c, m in back_edges} | {c for c, _m in back_edges}
    assert cyclic == reference_cyclic
    assert len(cyclic) > 40  # the census's pinned cycle scale

    walked = 0
    depth_checked = 0
    for type_id in product_ids:
        result = resolve_chain(type_id, 1, catalog, cyclic=cyclic)
        assert result.phases, f"type {type_id} resolved to nothing"
        walked += 1
        if result.cycles:
            # Every cut references an on-cycle material.
            assert all(cut.material_type_id in cyclic for cut in result.cycles)
            continue
        buildable_levels = sum(
            1
            for phase in result.phases
            if any(node.buildable for node in phase.nodes)
        )
        assert buildable_levels == reference_depth[type_id], (
            f"type {type_id}: app depth {buildable_levels}"
            f" vs reference {reference_depth[type_id]}"
        )
        depth_checked += 1

    assert walked == len(product_ids)
    # The overwhelming majority of the catalog never touches a cycle.
    assert depth_checked > walked * 0.9
