"""Admin SDE check tests: the change-detection engine (up-to-date,
changed-hash drop-and-reimport, unavailable MD5), the interval gate the
background loop honors across restarts, and the admin page/button.

The engine is exercised end to end against a fabricated dump served
gzipped over mocked HTTP — the same path the background loop and the
Check now button take."""

import asyncio
import gzip
import hashlib
import sqlite3
from urllib.parse import parse_qs, urlparse

import respx

from app.sde import (
    check_and_import,
    check_due,
    load_dump,
    record_check,
    request_cancel,
    sde_info,
)
from tests.conftest import token_response
from tests.test_sde_import import _make_dump

SSO_TOKEN_URL = "https://sso.test/v2/oauth/token"
DUMP_URL = "https://sde.test/latest-sqlite.db.gz"
MD5_URL = f"{DUMP_URL}.md5sum"

LAST_MODIFIED = "Fri, 13 Nov 2026 11:16:01 GMT"


def _serve_dump(dump_path) -> str:
    """respx routes: the gzipped dump and its published MD5 sidecar. The
    published hash matches the served bytes (one compression, reused).
    Returns the published MD5."""
    gz = gzip.compress(dump_path.read_bytes())
    md5 = hashlib.md5(gz).hexdigest()
    respx.get(DUMP_URL).respond(
        content=gz, headers={"Last-Modified": LAST_MODIFIED}
    )
    respx.get(MD5_URL).respond(text=f"{md5}  latest-sqlite.db.gz\n")
    return md5


async def _login(client):
    respx.post(SSO_TOKEN_URL).respond(json=token_response(name="Alpha Pilot"))
    response = await client.get("/auth/eve/login", follow_redirects=False)
    state = parse_qs(urlparse(response.headers["location"]).query)["state"][0]
    await client.get("/auth/eve/callback", params={"code": "abc", "state": state})


@respx.mock
def test_check_up_to_date(tmp_path):
    """A published MD5 matching the stored import reports up-to-date —
    no download, no re-import, but the check is recorded."""
    db_path = tmp_path / "target.db"
    dump_path = tmp_path / "dump.sqlite"
    _make_dump(dump_path)
    published = _serve_dump(dump_path)
    load_dump(db_path, dump_path, upstream_md5=published)

    status = check_and_import(db_path, dump_url=DUMP_URL, user_agent="test")

    assert status == "up-to-date"
    meta, counts = sde_info(db_path)
    assert meta["check_status"] == "up-to-date"
    assert meta["last_checked_at"] is not None
    # Nothing re-imported: the mirror is untouched.
    assert counts["sde_invTypes"] == 3


@respx.mock
def test_check_detects_change_and_reimports(tmp_path):
    """A changed published MD5 triggers the full drop-and-reimport: the
    mirror is replaced (not merged), provenance and check status land."""
    db_path = tmp_path / "target.db"
    old_dump = tmp_path / "old.sqlite"
    _make_dump(old_dump)
    load_dump(db_path, old_dump, upstream_md5="0" * 32)

    # Upstream now serves a dump with one extra type row.
    new_dump = tmp_path / "new.sqlite"
    _make_dump(new_dump)
    con = sqlite3.connect(new_dump)
    con.execute("INSERT INTO invTypes VALUES (999, 'New Type', 1.0, 1.0, 176, 1)")
    con.commit()
    con.close()
    _serve_dump(new_dump)

    status = check_and_import(db_path, dump_url=DUMP_URL, user_agent="test")

    assert status == "completed"
    con = sqlite3.connect(db_path)
    try:
        assert con.execute("SELECT COUNT(*) FROM sde_invTypes").fetchone()[0] == 4
        assert con.execute(
            "SELECT version FROM sde_meta WHERE id = 1"
        ).fetchone()[0] == "2026-11-13"  # from Last-Modified
    finally:
        con.close()
    meta, counts = sde_info(db_path)
    assert meta["check_status"] == "completed"
    assert counts["sde_invTypes"] == 4


@respx.mock
def test_check_failed_when_md5_unavailable(tmp_path):
    db_path = tmp_path / "target.db"
    respx.get(MD5_URL).respond(status_code=404)

    status = check_and_import(db_path, dump_url=DUMP_URL, user_agent="test")

    assert status == "failed"
    meta, _ = sde_info(db_path)
    assert meta["check_status"] == "failed"
    assert "unavailable" in meta["check_detail"]
    # The check still counts: the interval gate backs off.
    assert meta["last_checked_at"] is not None


def test_check_due_interval_gate(tmp_path):
    """The persisted last-checked timestamp gates the loop — a recent
    check is not due, a stale one is, and restarts can't reset it."""
    db_path = tmp_path / "target.db"
    assert check_due(db_path, 24)  # nothing checked yet

    record_check(db_path, status="up-to-date")
    assert not check_due(db_path, 24)
    assert check_due(db_path, 0)  # zero interval: always due

    # A stale timestamp is due again.
    con = sqlite3.connect(db_path)
    con.execute("UPDATE sde_meta SET last_checked_at = '2020-01-01 00:00:00'")
    con.commit()
    con.close()
    assert check_due(db_path, 24)


@respx.mock
async def test_admin_sde_page(client, app, tmp_path):
    await _login(client)
    db_path = tmp_path / "target.db"
    dump_path = tmp_path / "dump.sqlite"
    _make_dump(dump_path)
    load_dump(db_path, dump_path, source_url="https://example/dump")
    record_check(db_path, status="completed")
    app.state.settings = app.state.settings.model_copy(
        update={"database_url": f"sqlite+aiosqlite:///{db_path}"}
    )

    response = await client.get("/admin/sde")
    assert response.status_code == 200
    assert "SDE Data" in response.text
    assert "Last checked:" in response.text
    assert "import completed" in response.text
    assert "sde_invTypes" in response.text
    # The nav carries the Admin group with SDE Data active.
    assert 'href="/admin/sde" class="active"' in response.text


@respx.mock
async def test_admin_sde_check_button(client, app, tmp_path):
    await _login(client)
    db_path = tmp_path / "target.db"
    dump_path = tmp_path / "dump.sqlite"
    _make_dump(dump_path)
    published = _serve_dump(dump_path)
    load_dump(db_path, dump_path, upstream_md5=published)
    app.state.settings = app.state.settings.model_copy(
        update={
            "database_url": f"sqlite+aiosqlite:///{db_path}",
            "sde_dump_url": DUMP_URL,
        }
    )

    response = await client.post("/admin/sde/check", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/sde"

    # The background task runs the check; give it a beat to land.
    meta = None
    for _ in range(50):
        await asyncio.sleep(0.05)
        meta, _ = sde_info(db_path)
        if meta and meta["check_status"] in ("up-to-date", "completed", "failed"):
            break
    assert meta["check_status"] == "up-to-date"
    assert meta["last_checked_at"] is not None


@respx.mock
def test_import_now_forces_reimport(tmp_path):
    """Import now bypasses the MD5 comparison: even a matching hash
    performs the full download and re-import (the initial-import and
    manual-refresh path)."""
    db_path = tmp_path / "target.db"
    dump_path = tmp_path / "dump.sqlite"
    _make_dump(dump_path)
    published = _serve_dump(dump_path)
    load_dump(db_path, dump_path, upstream_md5=published)

    status = check_and_import(
        db_path, dump_url=DUMP_URL, user_agent="test", force=True
    )

    assert status == "completed"
    meta, _ = sde_info(db_path)
    assert meta["check_status"] == "completed"


@respx.mock
def test_stop_cancels_during_download(tmp_path):
    """A stop request lands between download chunks: the running check
    records a cancelled status and leaves the previous mirror intact."""
    import threading
    import time

    db_path = tmp_path / "target.db"
    dump_path = tmp_path / "dump.sqlite"
    _make_dump(dump_path)
    load_dump(db_path, dump_path, upstream_md5="0" * 32)


    def slow_content():
        yield b"x" * 16
        time.sleep(1.5)  # the stop lands while this is pending
        yield b"y" * 16

    respx.get(DUMP_URL).respond(
        content=slow_content(), headers={"Last-Modified": LAST_MODIFIED}
    )
    respx.get(MD5_URL).respond(text=f"{'9' * 32}  latest-sqlite.db.gz\n")
    threading.Timer(0.3, request_cancel).start()

    status = check_and_import(db_path, dump_url=DUMP_URL, user_agent="test")

    assert status == "cancelled"
    meta, counts = sde_info(db_path)
    assert meta["check_status"] == "cancelled"
    assert "stopped" in meta["check_detail"]
    # The previous mirror is untouched.
    assert counts["sde_invTypes"] == 3


def test_pause_and_import_exists_gating(tmp_path):
    """The loop only maintains an existing mirror: no import yet means
    no automatic checks, and the pause flag stops them entirely. The
    flag also survives a re-import."""
    from app.sde import import_exists, is_paused, set_paused

    db_path = tmp_path / "target.db"
    assert not import_exists(db_path)  # fresh deployment: admin's call

    dump_path = tmp_path / "dump.sqlite"
    _make_dump(dump_path)
    load_dump(db_path, dump_path)
    assert import_exists(db_path)

    set_paused(db_path, True)
    assert is_paused(db_path)

    # The pause flag is administrator state — a re-import keeps it.
    load_dump(db_path, dump_path)
    assert is_paused(db_path)

    set_paused(db_path, False)
    assert not is_paused(db_path)


@respx.mock
async def test_admin_import_pause_stop_routes(client, app, tmp_path):
    await _login(client)
    db_path = tmp_path / "target.db"
    dump_path = tmp_path / "dump.sqlite"
    _make_dump(dump_path)
    published = _serve_dump(dump_path)
    load_dump(db_path, dump_path, upstream_md5=published)
    app.state.settings = app.state.settings.model_copy(
        update={
            "database_url": f"sqlite+aiosqlite:///{db_path}",
            "sde_dump_url": DUMP_URL,
        }
    )

    # Pause / resume toggle.
    response = await client.post("/admin/sde/pause", follow_redirects=False)
    assert response.status_code == 303
    from app.sde import is_paused

    assert is_paused(db_path)
    response = await client.post("/admin/sde/pause", follow_redirects=False)
    assert response.status_code == 303
    assert not is_paused(db_path)

    # Import now: forced — completes even though the MD5 matches.
    response = await client.post("/admin/sde/import", follow_redirects=False)
    assert response.status_code == 303
    meta = None
    for _ in range(50):
        await asyncio.sleep(0.05)
        meta, _ = sde_info(db_path)
        if meta and meta["check_status"] in ("completed", "failed"):
            break
    assert meta["check_status"] == "completed"

    # Stop with nothing running: harmless no-op.
    response = await client.post("/admin/sde/stop", follow_redirects=False)
    assert response.status_code == 303
