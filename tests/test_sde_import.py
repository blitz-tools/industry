"""SDE import tests: the load path against a fabricated dump shaped like
the fuzzwork SQLite export. The sde_* namespace must be a VERBATIM
mirror — same columns, same rows, duplicates included — so these tests
pin copy fidelity, atomic replacement, and provenance stamping. The
network download stays thin and untested; `--file` exercises everything
it feeds."""

import sqlite3
from pathlib import Path

import pytest

from app.sde import is_current, load_dump, resolve_db_path, sde_info

# A minimal-but-real slice of the SDE in its own column names: a
# Typhoon-ish blueprint with manufacturing materials/products/skills and
# an invention probability — including the duplicate skill row the
# published dump actually carries.
DUMP_ROWS = {
    "invTypes": [
        (998, "Typhoon Blueprint", 0.01, 0.01, 176, 1),
        (644, "Typhoon", 245000.0, 245000.0, 26, 1),
        (34, "Tritanium", 0.01, 0.01, 18, 1),
    ],
    "invGroups": [(176, "Blueprint", 9), (26, "Battleship", 6)],
    "invCategories": [(9, "Blueprint"), (6, "Ship")],
    "industryBlueprints": [(998, 10)],
    "ramActivities": [(1, "Manufacturing"), (8, "Invention")],
    "industryActivity": [(998, 1, 18000), (998, 8, 12000)],
    "industryActivityMaterials": [(998, 1, 34, 8000000), (998, 8, 20410, 4)],
    "industryActivityProducts": [(998, 1, 644, 1)],
    "industryActivitySkills": [
        (998, 1, 3380, 1),
        (998, 1, 3380, 1),  # the real dump carries exact duplicates
        (998, 8, 11433, 1),
    ],
    "industryActivityProbabilities": [(998, 8, 644, 0.34)],
}

SOURCE_COLUMNS = {
    "invTypes": ["typeID", "typeName", "volume", "packagedVolume", "groupID",
                 "published"],
    "invGroups": ["groupID", "groupName", "categoryID"],
    "invCategories": ["categoryID", "categoryName"],
    "industryBlueprints": ["typeID", "maxProductionLimit"],
    "ramActivities": ["activityID", "activityName"],
    "industryActivity": ["typeID", "activityID", "time"],
    "industryActivityMaterials": ["typeID", "activityID", "materialTypeID",
                                  "quantity"],
    "industryActivityProducts": ["typeID", "activityID", "productTypeID",
                                 "quantity"],
    "industryActivitySkills": ["typeID", "activityID", "skillID", "level"],
    "industryActivityProbabilities": ["typeID", "activityID", "productTypeID",
                                      "probability"],
}


def _make_dump(path: Path) -> None:
    con = sqlite3.connect(path)
    try:
        for table, columns in SOURCE_COLUMNS.items():
            con.execute(
                f"CREATE TABLE {table} ({', '.join(columns)})"
            )
            con.executemany(
                f"INSERT INTO {table} VALUES ({','.join('?' * len(columns))})",
                DUMP_ROWS[table],
            )
        con.commit()
    finally:
        con.close()


@pytest.fixture
def dump_file(tmp_path) -> Path:
    dump_path = tmp_path / "dump.sqlite"
    _make_dump(dump_path)
    return dump_path


def test_load_dump_mirrors_verbatim(tmp_path, dump_file):
    """The mirror carries the dump's own column names and every row —
    duplicates included. No reshaping happens in the import."""
    db_path = tmp_path / "target.db"
    counts = load_dump(
        db_path, dump_file, source_url="https://example/dump",
        dump_sha256="abc123", version="2026-11-13",
    )

    con = sqlite3.connect(db_path)
    try:
        for table, columns in SOURCE_COLUMNS.items():
            mirror = f"sde_{table}"
            got_columns = [c[1] for c in con.execute(f"PRAGMA table_info({mirror})")]
            assert got_columns == columns, mirror
            assert counts[mirror] == len(DUMP_ROWS[table])
        # Verbatim rows, dump column names and all.
        row = con.execute(
            "SELECT typeID, typeName, volume FROM sde_invTypes WHERE typeID = 644"
        ).fetchone()
        assert row == (644, "Typhoon", 245000.0)
        # The duplicate skill row survives — dedup belongs to consumers.
        assert con.execute(
            "SELECT COUNT(*) FROM sde_industryActivitySkills "
            "WHERE typeID = 998 AND activityID = 1 AND skillID = 3380"
        ).fetchone()[0] == 2
        # Provenance stamped.
        meta = con.execute(
            "SELECT version, source_url, dump_sha256 FROM sde_meta WHERE id = 1"
        ).fetchone()
        assert meta == ("2026-11-13", "https://example/dump", "abc123")
    finally:
        con.close()


def test_load_dump_replaces_atomically(tmp_path, dump_file):
    """Re-loading swaps the mirror in place, and a failure mid-load (a
    source table missing from a new dump) leaves the previous mirror
    intact."""
    db_path = tmp_path / "target.db"
    load_dump(db_path, dump_file, source_url="first")
    counts = load_dump(db_path, dump_file, source_url="second")
    assert counts["sde_invTypes"] == 3  # not 6

    broken = dump_file.with_name("broken.sqlite")
    _make_dump(broken)
    con = sqlite3.connect(broken)
    con.execute("DROP TABLE industryActivityProducts")
    con.commit()
    con.close()
    with pytest.raises(sqlite3.OperationalError):
        load_dump(db_path, broken, source_url="broken")

    con = sqlite3.connect(db_path)
    try:
        assert con.execute("SELECT COUNT(*) FROM sde_invTypes").fetchone()[0] == 3
        assert con.execute(
            "SELECT source_url FROM sde_meta WHERE id = 1"
        ).fetchone()[0] == "second"
    finally:
        con.close()


def test_sde_info(tmp_path, dump_file):
    db_path = tmp_path / "target.db"
    meta, counts = sde_info(db_path)
    assert meta is None
    assert counts["sde_invTypes"] == -1  # not imported yet

    load_dump(db_path, dump_file, source_url="https://example/dump",
              dump_sha256="abc123")
    meta, counts = sde_info(db_path)
    assert meta["source_url"] == "https://example/dump"
    assert counts["sde_industryActivitySkills"] == 3  # duplicate included


def test_is_current_change_detection(tmp_path, dump_file):
    """The published-MD5 check: no import yet → not current; matching
    hash → current; changed hash → not current."""
    db_path = tmp_path / "target.db"
    assert not is_current(db_path, "d41d8cd98f00b204e9800998ecf8427e")

    load_dump(db_path, dump_file, source_url="url", upstream_md5="a" * 32)
    assert is_current(db_path, "a" * 32)
    assert not is_current(db_path, "b" * 32)  # upstream changed
    assert not is_current(db_path, None)  # sidecar unavailable


def test_resolve_db_path():
    assert resolve_db_path("sqlite+aiosqlite:////app/industry.db") == Path(
        "/app/industry.db"
    )
    assert resolve_db_path("sqlite+aiosqlite:///./industry.db") == Path(
        "./industry.db"
    )
    with pytest.raises(SystemExit, match="file-backed"):
        resolve_db_path("sqlite+aiosqlite://")
    with pytest.raises(SystemExit, match="Unsupported"):
        resolve_db_path("postgresql://nope")
