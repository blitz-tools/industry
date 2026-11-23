"""Catalog query layer tests (M2): commodity search, recipe reads, and
the owned-blueprint overlay over the verbatim SDE mirror. The sde_*
tables have no ORM models by design — the fixture creates them with raw
DDL in the dump's own column shapes and seeds a slice that carries the
real mirror's quirks: an unpublished CCP test artifact sitting first by
rowid (the prefer-published producer rule), an exact-duplicate skill
row, an invention-only product (excluded from the catalog), and an
orphan product row whose type lives only in universe_types (the name
merge rule's fallback path)."""

from datetime import timedelta

import pytest_asyncio
from sqlalchemy import text

from app.db import utc_now
from app.esi.assets import OWNER_CHARACTER, OWNER_CORPORATION
from app.industry import commodity_recipe, owned_blueprints_for_type, search_catalog
from app.models import (
    Asset,
    Blueprint,
    Character,
    UniverseCorporation,
    UniverseLocation,
    UniverseType,
)

# The dump's own column shapes (tests/test_sde_import.py keeps the full
# list; these are the tables the catalog layer reads).
SDE_DDL = (
    "CREATE TABLE sde_invTypes (typeID INTEGER PRIMARY KEY, typeName TEXT,"
    " volume REAL, packagedVolume REAL, groupID INTEGER, published INTEGER)",
    "CREATE TABLE sde_invGroups (groupID INTEGER PRIMARY KEY, groupName TEXT,"
    " categoryID INTEGER)",
    "CREATE TABLE sde_invCategories (categoryID INTEGER PRIMARY KEY,"
    " categoryName TEXT)",
    "CREATE TABLE sde_industryBlueprints (typeID INTEGER PRIMARY KEY,"
    " maxProductionLimit INTEGER)",
    "CREATE TABLE sde_industryActivity (typeID INTEGER, activityID INTEGER,"
    " time INTEGER)",
    "CREATE TABLE sde_industryActivityMaterials (typeID INTEGER,"
    " activityID INTEGER, materialTypeID INTEGER, quantity INTEGER)",
    "CREATE TABLE sde_industryActivityProducts (typeID INTEGER,"
    " activityID INTEGER, productTypeID INTEGER, quantity INTEGER)",
    "CREATE TABLE sde_industryActivitySkills (typeID INTEGER,"
    " activityID INTEGER, skillID INTEGER, level INTEGER)",
)

SDE_ROWS = {
    "sde_invTypes": [
        (998, "Typhoon Blueprint", 0.01, 0.01, 176, 1),
        (644, "Typhoon", 245000.0, 245000.0, 26, 1),
        (32312, "Typhoon Fleet Issue Blueprint", 0.01, 0.01, 176, 1),
        (32311, "Typhoon Fleet Issue", 245000.0, 245000.0, 26, 1),
        (20186, "Charon Blueprint", 0.01, 0.01, 176, 1),
        (20185, "Charon", 900000.0, 900000.0, 26, 1),
        (34, "Tritanium", 0.01, 0.01, 18, 1),
        (20411, "Capital Power Generator Blueprint", 0.01, 0.01, 176, 1),
        (20410, "Capital Power Generator", 100.0, 100.0, 33, 1),
        (3380, "Industry", 0.01, 0.01, 269, 1),
        (22242, "Advanced Industry", 0.01, 0.01, 269, 1),
        (22441, "Panther Blueprint", 0.01, 0.01, 176, 1),
        # The real dump's test artifact: unpublished, and its product row
        # sits first by rowid (insertion order below mirrors that).
        (45732, "Test Reaction Blueprint", 0.01, 0.01, 176, 0),
        (46207, "Tungsten Carbide Reaction Formula", 0.01, 0.01, 176, 1),
        (16672, "Tungsten Carbide", 0.1, 0.1, 28, 1),
        (88888, "Orphan Producer Blueprint", 0.01, 0.01, 176, 1),
        # typeID 99999 is deliberately absent: the orphan product row
        # references it, and only universe_types names it.
    ],
    "sde_invGroups": [
        (176, "Blueprint", 9),
        (26, "Battleship", 6),
        (18, "Mineral", 4),
        (33, "Capital Component", 6),
        (269, "Skills", 16),
        (28, "Composite", 16),
    ],
    "sde_invCategories": [(9, "Blueprint"), (6, "Ship"), (4, "Material"),
                          (16, "Misc")],
    "sde_industryBlueprints": [(998, 10), (46207, 1000), (20411, 600)],
    "sde_industryActivity": [(998, 1, 18000), (998, 8, 12000)],
    "sde_industryActivityMaterials": [
        (998, 1, 34, 8000000),
        (998, 1, 20410, 55),
    ],
    "sde_industryActivityProducts": [
        (998, 1, 644, 1),
        # Invention output: a blueprint, never a catalog commodity.
        (998, 8, 22441, 1),
        (32312, 1, 32311, 1),
        (20186, 1, 20185, 1),
        (20411, 1, 20410, 3),
        # The test artifact's row lands first by rowid; the published
        # formula must still win the producer slot.
        (45732, 11, 16672, 20),
        (46207, 11, 16672, 10000),
        # Orphan products: typeID 99999 has no invTypes row (named only
        # by universe_types); 77777 has no name anywhere — it must stay
        # in the catalog under its #id fallback, never silently drop.
        (88888, 1, 99999, 1),
        (88888, 1, 77777, 1),
    ],
    "sde_industryActivitySkills": [
        (998, 1, 3380, 1),
        (998, 1, 3380, 1),  # the dump carries exact duplicates
        (998, 1, 22242, 3),
    ],
}


@pytest_asyncio.fixture
async def catalog_db(db_session):
    """The SDE slice plus the live tables the overlay joins."""
    for ddl in SDE_DDL:
        await db_session.execute(text(ddl))
    for table, rows in SDE_ROWS.items():
        columns = range(len(rows[0]))
        marks = ", ".join(f":c{i}" for i in columns)
        await db_session.execute(
            text(f"INSERT INTO {table} VALUES ({marks})"),
            [
                {f"c{i}": value for i, value in enumerate(row)}
                for row in rows
            ],
        )
    db_session.add_all([
        Character(
            character_id=1234,
            name="Test Pilot",
            owner_hash="owner-1",
            scopes="publicData",
            access_token="tok",
            access_token_expires_at=utc_now() + timedelta(minutes=30),
            refresh_token="R",
        ),
        # Name-merge-rule rows: universe names that must NOT override
        # the SDE (the live mirror's one differing name is exactly this
        # shape — a trailing space).
        UniverseType(type_id=99999, name="Universe-Only Product"),
        UniverseType(type_id=644, name="Typhoon "),
        UniverseType(type_id=998, name="Stale Blueprint Name"),
        UniverseLocation(
            location_id=60003743,
            kind="station",
            name="Jita IV - Moon 4 CPF",
        ),
        UniverseCorporation(corporation_id=98000001, name="Federal Freight"),
        # The BPC's location is a container item id: the overlay names it
        # through the owner's asset snapshot hop (item → parent).
        Asset(
            owner_type=OWNER_CHARACTER,
            owner_id=1234,
            item_id=5000,
            type_id=12345,
            quantity=1,
            location_id=60003743,
            location_flag="Cargo",
            location_type="item",
            parent_location_id=60003743,
            is_blueprint_copy=False,
            is_singleton=True,
        ),
        Blueprint(
            owner_type=OWNER_CORPORATION,
            owner_id=98000001,
            item_id=1001,
            type_id=998,
            location_id=60003743,
            location_flag="CorpSAG2",
            quantity=1,
            runs=-1,
            material_efficiency=10,
            time_efficiency=20,
        ),
        Blueprint(
            owner_type=OWNER_CHARACTER,
            owner_id=1234,
            item_id=1002,
            type_id=998,
            location_id=5000,
            location_flag="Cargo",
            quantity=1,
            runs=15,
            material_efficiency=2,
            time_efficiency=4,
        ),
    ])
    await db_session.commit()
    return db_session


async def test_search_matches_products_with_owned_overlay(catalog_db):
    """The autocomplete row: built commodity first (prefix beats
    substring), producer blueprint and max limit derived, owned counts
    across the whole pool."""
    entries = await search_catalog(catalog_db, "typh")
    assert [e.type_name for e in entries] == ["Typhoon", "Typhoon Fleet Issue"]
    typhoon = entries[0]
    assert typhoon.type_id == 644
    assert typhoon.group_name == "Battleship"
    assert typhoon.blueprint_type_id == 998
    assert typhoon.blueprint_name == "Typhoon Blueprint"
    assert typhoon.activity_id == 1
    assert typhoon.activity_label == "Manufacturing"
    assert typhoon.products_per_run == 1
    assert typhoon.max_production_limit == 10
    assert typhoon.owned_originals == 1  # the corporation BPO
    assert typhoon.owned_copies == 1  # the character BPC


async def test_search_excludes_invention_products(catalog_db):
    """Invention outputs are blueprints, not catalog commodities — the
    Panther Blueprint's only product row is activity 8."""
    assert await search_catalog(catalog_db, "panther") == []


async def test_search_prefers_published_producer(catalog_db):
    """The unpublished CCP test artifact sits first by rowid; the
    producer slot goes to the published formula."""
    (entry,) = await search_catalog(catalog_db, "tungsten")
    assert entry.blueprint_type_id == 46207
    assert entry.blueprint_name == "Tungsten Carbide Reaction Formula"
    assert entry.activity_id == 11
    assert entry.activity_label == "Reaction"
    assert entry.products_per_run == 10000
    assert entry.max_production_limit == 1000
    assert entry.owned_count == 0


async def test_search_owned_only_filters_to_inventory(catalog_db):
    """Match From Inventory keeps products with any blueprint in the
    pool: the Typhoon (owned bp 998) stays, the Charon drops."""
    names = {e.type_name for e in await search_catalog(catalog_db, "", owned_only=True)}
    assert "Typhoon" in names
    assert "Charon" not in names


async def test_search_universe_fallback_names_orphan_products(catalog_db):
    """A product row whose type the dump lacks names through
    universe_types (the merge rule's fallback path)."""
    (entry,) = await search_catalog(catalog_db, "universe-only")
    assert entry.type_id == 99999
    assert entry.type_name == "Universe-Only Product"
    assert entry.blueprint_type_id == 88888
    assert entry.max_production_limit is None  # no industryBlueprints row


async def test_search_enumerates_full_catalog_with_id_fallback(catalog_db):
    """Empty-pattern search enumerates every catalog member (the census
    membership rule, counted at query time), and a product with no name
    anywhere stays in under its #id fallback — a NULL name must never
    silently drop a member (SQL NULL LIKE excludes it)."""
    entries = await search_catalog(catalog_db, "", limit=100)
    assert {e.type_id for e in entries} == {
        644,  # Typhoon
        32311,  # Typhoon Fleet Issue
        20185,  # Charon
        20410,  # Capital Power Generator
        16672,  # Tungsten Carbide
        99999,  # orphan, universe-named
        77777,  # orphan, nameless
    }
    (nameless,) = [e for e in entries if e.type_id == 77777]
    assert nameless.type_name == "#77777"


async def test_search_sde_name_wins_over_universe(catalog_db):
    """Where both name sources hold the type, the SDE name displays —
    the universe row's trailing space must not leak."""
    (entry,) = await search_catalog(catalog_db, "typhoon", limit=1)
    assert entry.type_name == "Typhoon"


async def test_recipe_reads_typhoon_end_to_end(catalog_db):
    """The M4 calculator's inputs: per-run materials flagged for chain
    continuation, deduped skills, duration, max limit, and the owned
    overlay with ME/TE/runs per copy."""
    recipe = await commodity_recipe(catalog_db, 644)
    assert recipe is not None
    assert recipe.blueprint_type_id == 998
    assert recipe.products_per_run == 1
    assert recipe.max_production_limit == 10
    assert recipe.duration_seconds == 18000
    # Quantity-ordered; the component carries the chain-continuation
    # flag the M5 resolver recurses on.
    assert [(m.name, m.quantity_per_run, m.buildable) for m in recipe.materials] == [
        ("Tritanium", 8000000, False),
        ("Capital Power Generator", 55, True),
    ]
    # The dump's duplicate skill row dedups to one entry per skill.
    assert [(s.name, s.level) for s in recipe.skills] == [
        ("Advanced Industry", 3),
        ("Industry", 1),
    ]
    # Owned overlay: the corporation original and the character copy,
    # each with its synced ME/TE, owner name, and resolved location
    # (the BPC's container hops to its parent station).
    assert [(o.owner_name, o.runs, o.material_efficiency, o.location_name)
            for o in recipe.owned] == [
        ("Federal Freight", -1, 10, "Jita IV - Moon 4 CPF"),
        ("Test Pilot", 15, 2, "Jita IV - Moon 4 CPF"),
    ]
    assert all(o.type_name == "Typhoon Blueprint" for o in recipe.owned)
    assert [o.icon_kind for o in recipe.owned] == ["bp", "bpc"]


async def test_recipe_none_outside_catalog(catalog_db):
    """Raw types (no producer) and invention outputs (activity 8 only)
    are not catalog commodities."""
    assert await commodity_recipe(catalog_db, 34) is None
    assert await commodity_recipe(catalog_db, 22441) is None


async def test_owned_blueprints_for_type_names_across_pool(catalog_db):
    """The overlay read on its own: every owner of the blueprint type,
    SDE name preferred over the stale universe row."""
    rows = await owned_blueprints_for_type(catalog_db, 998)
    assert len(rows) == 2
    assert {r.owner_name for r in rows} == {"Test Pilot", "Federal Freight"}
    assert all(r.type_name == "Typhoon Blueprint" for r in rows)
