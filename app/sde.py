"""SDE import: mirror the EVE static data export into sde_* tables.

The recipe data the planner needs (what blueprints build from and
produce, their skills and durations) is not served by ESI — it lives in
the SDE. This module is the managed import from MILESTONES.md M2:

    podman compose -f compose.dev.yml run --rm dev python -m app.sde import
    podman compose -f compose.dev.yml run --rm dev python -m app.sde info

The sde_* namespace is a **verbatim mirror** of the dump's tables:
same columns, same rows — duplicates included — created by the import
itself (`DROP` + `CREATE TABLE AS SELECT`), so a dump schema change can
never break the import and nothing in the app schema (alembic) knows
about it. Interpreting the data (blueprint→product mappings, skill
dedup, activity labels) belongs to the consuming query layer, never
here.

`import` checks the published dump MD5 first (one tiny request) and
exits without downloading when the release is unchanged; otherwise it
fetches fuzzwork's gzipped SQLite dump and replaces the mirror in one
transaction. A local file can be loaded with --file. Provenance
(release date from Last-Modified, source URL, content hash, import
timestamp) lands in sde_meta.

Synchronous by design: a batch job, not request-path code. It writes to
the same SQLite database the app uses; run it while the app is stopped
or quiet (SQLite locks per write transaction, and the import's single
transaction is short compared to the download).
"""

import argparse
import asyncio
import gzip
import hashlib
import logging
import shutil
import sqlite3
import tempfile
import threading
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path

import httpx

from .config import get_settings

logger = logging.getLogger(__name__)

# The dump tables mirrored into sde_<name>. The list is the only static
# part — each mirror's shape comes from the dump itself.
MIRROR_TABLES: tuple[str, ...] = (
    "invTypes",
    "invGroups",
    "invCategories",
    "industryBlueprints",
    "ramActivities",
    "industryActivity",
    "industryActivityMaterials",
    "industryActivityProducts",
    "industryActivitySkills",
    "industryActivityProbabilities",
)

META_TABLE = "sde_meta"

# The admin-section background check: how often the loop re-evaluates
# whether a check is due (the interval itself lives in settings).
CHECK_POLL_SECONDS = 3600

# One check/import at a time (loop vs admin button).
_import_lock = threading.Lock()
_import_running = threading.Event()
# Cooperative cancellation for the admin Stop button: checked at phase
# boundaries and between download chunks.
_cancel_requested = threading.Event()


class ImportCancelled(Exception):
    """The administrator stopped a running check/import."""


def request_cancel() -> None:
    """Ask the running check/import (if any) to stop at the next
    boundary; a run that is already cancelled stays cancelled."""
    _cancel_requested.set()


def _cancel_pending() -> bool:
    return _cancel_requested.is_set()


def resolve_db_path(database_url: str) -> Path:
    """The SQLite file behind the app's async database URL."""
    prefix = "sqlite+aiosqlite://"
    if not database_url.startswith(prefix):
        raise SystemExit(f"Unsupported database URL for SDE import: {database_url}")
    rest = database_url[len(prefix) :]
    if not rest.strip("/"):
        raise SystemExit("The SDE import needs a file-backed database, not :memory:")
    if rest.startswith("//"):
        return Path(rest[1:])  # four slashes: absolute path
    return Path(rest.lstrip("/"))


def fetch_upstream_md5(dump_url: str, *, user_agent: str) -> str | None:
    """The published MD5 of the dump archive (dump_url + '.md5sum'), for
    change detection without a download. None when the sidecar file is
    unavailable — the import then just proceeds."""
    try:
        response = httpx.get(
            f"{dump_url}.md5sum", headers={"User-Agent": user_agent},
            follow_redirects=True, timeout=30.0,
        )
        response.raise_for_status()
    except httpx.HTTPError:
        return None
    token = response.text.split()[0] if response.text.split() else None
    return token if token and len(token) == 32 else None


def is_current(db_path: Path, upstream_md5: str | None) -> bool:
    """True when the stored import already matches the published MD5 —
    nothing new upstream, no download needed."""
    if upstream_md5 is None or not db_path.exists():
        return False
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        try:
            row = con.execute(
                f"SELECT upstream_md5 FROM {META_TABLE} WHERE id = 1"
            ).fetchone()
        except sqlite3.OperationalError:
            return False
        return row is not None and row[0] == upstream_md5
    finally:
        con.close()


def download_dump(
    url: str,
    dest_dir: Path,
    *,
    user_agent: str,
    cancel_check=None,
) -> tuple[Path, str, str, str | None]:
    """Stream the gzipped dump to dest_dir; returns (path, sha256, md5,
    Last-Modified). The md5 is verified against the published .md5sum by
    the caller; the hashes and date together identify what was imported
    (the URL itself is stable across releases). `cancel_check` is polled
    between chunks so a stop request lands within seconds."""
    dest = dest_dir / "sde-dump.db.gz"
    sha256 = hashlib.sha256()
    md5 = hashlib.md5()
    with httpx.Client(follow_redirects=True, timeout=60.0) as client:
        with client.stream("GET", url, headers={"User-Agent": user_agent}) as response:
            response.raise_for_status()
            last_modified = response.headers.get("Last-Modified")
            with open(dest, "wb") as fh:
                for chunk in response.iter_bytes(chunk_size=1 << 20):
                    if cancel_check and cancel_check():
                        raise ImportCancelled
                    fh.write(chunk)
                    sha256.update(chunk)
                    md5.update(chunk)
    return dest, sha256.hexdigest(), md5.hexdigest(), last_modified


def _release_date(last_modified: str | None) -> str | None:
    """The dump's Last-Modified as an ISO date — the release identity for
    a stable-URL source."""
    if not last_modified:
        return None
    try:
        return parsedate_to_datetime(last_modified).date().isoformat()
    except (TypeError, ValueError):
        return None


def _decompress(gz_path: Path, dest_dir: Path) -> Path:
    """The dump arrives gzip-compressed; SQLite needs a plain file."""
    dest = dest_dir / "sde-dump.sqlite"
    with gzip.open(gz_path, "rb") as src, open(dest, "wb") as out:
        shutil.copyfileobj(src, out, length=1 << 20)
    return dest


def load_dump(
    db_path: Path,
    dump_path: Path,
    *,
    source_url: str | None = None,
    dump_sha256: str | None = None,
    upstream_md5: str | None = None,
    version: str | None = None,
) -> dict[str, int]:
    """Replace the sde_* mirror from an SDE SQLite dump, atomically: each
    table is dropped and recreated as a verbatim structural copy
    (`CREATE TABLE AS SELECT`), so the mirror's columns and rows are
    exactly what the dump provides. One transaction — a failure leaves
    the previous mirror intact."""
    con = sqlite3.connect(db_path, isolation_level=None)
    try:
        con.execute("ATTACH DATABASE ? AS sdedump", (str(dump_path),))
        try:
            con.execute("BEGIN")
            for table in MIRROR_TABLES:
                mirror = f"sde_{table}"
                con.execute(f"DROP TABLE IF EXISTS {mirror}")
                con.execute(f"CREATE TABLE {mirror} AS SELECT * FROM sdedump.{table}")
            # The pause flag is administrator state, not import data —
            # carry it across the wholesale meta replacement.
            paused = _read_paused(con)
            con.execute(f"DROP TABLE IF EXISTS {META_TABLE}")
            con.execute(
                f"CREATE TABLE {META_TABLE} ("
                "id INTEGER PRIMARY KEY, version TEXT, source_url TEXT, "
                "dump_sha256 TEXT, upstream_md5 TEXT, imported_at TEXT, "
                "last_checked_at TEXT, check_status TEXT, check_detail TEXT, "
                "paused INTEGER DEFAULT 0)"
            )
            con.execute(
                f"INSERT INTO {META_TABLE} "
                "(id, version, source_url, dump_sha256, upstream_md5, "
                "imported_at, paused) VALUES (1, ?, ?, ?, ?, ?, ?)",
                (
                    version,
                    source_url,
                    dump_sha256,
                    upstream_md5,
                    datetime.now(UTC).replace(tzinfo=None).isoformat(
                        sep=" ", timespec="seconds"
                    ),
                    1 if paused else 0,
                ),
            )
            con.execute("COMMIT")
        except BaseException:
            con.execute("ROLLBACK")
            raise
        finally:
            con.execute("DETACH DATABASE sdedump")
        return {f"sde_{t}": _count(con, f"sde_{t}") for t in MIRROR_TABLES}
    finally:
        con.close()


def _count(con: sqlite3.Connection, table: str) -> int:
    try:
        return con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    except sqlite3.OperationalError:
        return -1  # not imported yet


def sde_info(db_path: Path) -> tuple[dict[str, str | None] | None, dict[str, int]]:
    """(sde_meta row as a dict, per-table counts) for the info and admin
    pages. Tolerates an older sde_meta schema (check fields read as
    None until the first background check normalizes it)."""
    if not db_path.exists():
        return None, {f"sde_{t}": -1 for t in MIRROR_TABLES}
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        meta_row = None
        for columns in (
            "version, source_url, dump_sha256, imported_at, "
            "last_checked_at, check_status, check_detail, paused",
            "version, source_url, dump_sha256, imported_at, "
            "last_checked_at, check_status, check_detail",  # pre-pause schema
            "version, source_url, dump_sha256, imported_at",  # pre-check schema
        ):
            try:
                meta_row = con.execute(
                    f"SELECT {columns} FROM {META_TABLE} WHERE id = 1"
                ).fetchone()
                break
            except sqlite3.OperationalError:
                continue
        meta = None
        if meta_row is not None:
            meta = {
                "version": meta_row[0],
                "source_url": meta_row[1],
                "dump_sha256": meta_row[2],
                "imported_at": meta_row[3],
                "last_checked_at": meta_row[4] if len(meta_row) > 4 else None,
                "check_status": meta_row[5] if len(meta_row) > 5 else None,
                "check_detail": meta_row[6] if len(meta_row) > 6 else None,
                "paused": bool(meta_row[7]) if len(meta_row) > 7 else False,
            }
        counts = {f"sde_{t}": _count(con, f"sde_{t}") for t in MIRROR_TABLES}
        return meta, counts
    finally:
        con.close()


def _read_paused(con: sqlite3.Connection) -> bool:
    """The pause flag from an existing sde_meta, if present."""
    try:
        columns = {row[1] for row in con.execute(f"PRAGMA table_info({META_TABLE})")}
    except sqlite3.OperationalError:
        return False
    if "paused" not in columns:
        return False
    row = con.execute(f"SELECT paused FROM {META_TABLE} WHERE id = 1").fetchone()
    return bool(row and row[0])


def ensure_sde_meta(db_path: Path) -> None:
    """Normalize an existing sde_meta to the current shape (adds the
    check and pause columns, creates the row). The import creates the
    table fresh each run; this covers databases whose last import
    predates the newer fields."""
    con = sqlite3.connect(db_path, isolation_level=None)
    try:
        try:
            columns = {row[1] for row in con.execute(f"PRAGMA table_info({META_TABLE})")}
        except sqlite3.OperationalError:
            columns = set()
        if not columns:
            con.execute(
                f"CREATE TABLE IF NOT EXISTS {META_TABLE} ("
                "id INTEGER PRIMARY KEY, version TEXT, source_url TEXT, "
                "dump_sha256 TEXT, upstream_md5 TEXT, imported_at TEXT, "
                "last_checked_at TEXT, check_status TEXT, check_detail TEXT, "
                "paused INTEGER DEFAULT 0)"
            )
        else:
            for column in ("last_checked_at", "check_status", "check_detail"):
                if column not in columns:
                    con.execute(f"ALTER TABLE {META_TABLE} ADD COLUMN {column} TEXT")
            if "paused" not in columns:
                con.execute(
                    f"ALTER TABLE {META_TABLE} ADD COLUMN paused INTEGER DEFAULT 0"
                )
        con.execute(f"INSERT OR IGNORE INTO {META_TABLE} (id) VALUES (1)")
    finally:
        con.close()


def import_exists(db_path: Path) -> bool:
    """True once an SDE set has been imported — the background loop only
    maintains an existing mirror; the initial import is the
    administrator's call (Import now or the CLI)."""
    if not db_path.exists():
        return False
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        try:
            row = con.execute(
                f"SELECT imported_at FROM {META_TABLE} WHERE id = 1"
            ).fetchone()
        except sqlite3.OperationalError:
            return False
        return row is not None and row[0] is not None
    finally:
        con.close()


def is_paused(db_path: Path) -> bool:
    """True when the administrator paused automatic imports."""
    if not db_path.exists():
        return False
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        return _read_paused(con)
    finally:
        con.close()


def set_paused(db_path: Path, value: bool) -> None:
    ensure_sde_meta(db_path)
    con = sqlite3.connect(db_path, isolation_level=None)
    try:
        con.execute(
            f"UPDATE {META_TABLE} SET paused = ? WHERE id = 1",
            (1 if value else 0,),
        )
    finally:
        con.close()


def record_check(db_path: Path, *, status: str, detail: str | None = None) -> None:
    """Stamp the check outcome onto sde_meta (creating the row/table when
    needed, so even a never-imported database records its checks)."""
    ensure_sde_meta(db_path)
    con = sqlite3.connect(db_path, isolation_level=None)
    try:
        con.execute(
            f"UPDATE {META_TABLE} SET last_checked_at = ?, check_status = ?, "
            "check_detail = ? WHERE id = 1",
            (
                datetime.now(UTC).replace(tzinfo=None).isoformat(
                    sep=" ", timespec="seconds"
                ),
                status,
                detail,
            ),
        )
    finally:
        con.close()


def check_due(db_path: Path, interval_hours: int) -> bool:
    """True when no check has run within the interval — the 'at most once
    a day' gate for the background loop (restarts don't reset it)."""
    if not db_path.exists():
        return True
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        try:
            row = con.execute(
                f"SELECT last_checked_at FROM {META_TABLE} WHERE id = 1"
            ).fetchone()
        except sqlite3.OperationalError:
            return True
    finally:
        con.close()
    if row is None or row[0] is None:
        return True
    try:
        checked = datetime.fromisoformat(row[0])
    except ValueError:
        return True
    return datetime.now(UTC).replace(tzinfo=None) - checked >= timedelta(
        hours=interval_hours
    )


def import_in_progress() -> bool:
    """Whether a check/import is running right now (in-process flag)."""
    return _import_running.is_set()


def check_and_import(
    db_path: Path,
    *,
    dump_url: str,
    user_agent: str,
    force: bool = False,
) -> str:
    """The admin-section check: fetch the published MD5, compare with the
    stored import, and on change drop-and-reimport the whole mirror (no
    diffing — the mirror is cheap to rebuild). The MD5 comparison is
    honored unless `force` (the Import now button — for the initial
    import or a manual refresh); only the background loop's interval
    gate decides WHEN to check automatically. Returns "up-to-date",
    "completed", "cancelled", "failed", or "in-progress" when another
    check holds the lock. The check timestamp is stamped at the START of
    the attempt, so a killed attempt still backs off for the interval."""
    if not _import_lock.acquire(blocking=False):
        return "in-progress"
    _import_running.set()
    _cancel_requested.clear()
    try:
        record_check(db_path, status="in-progress")
        if _cancel_pending():
            record_check(db_path, status="cancelled")
            return "cancelled"
        md5 = fetch_upstream_md5(dump_url, user_agent=user_agent)
        if _cancel_pending():
            record_check(db_path, status="cancelled")
            return "cancelled"
        if md5 is None:
            record_check(
                db_path, status="failed", detail="Published MD5 unavailable"
            )
            return "failed"
        if not force and is_current(db_path, md5):
            record_check(db_path, status="up-to-date")
            return "up-to-date"
        with tempfile.TemporaryDirectory(prefix="sde-check-") as tmp:
            tmp_dir = Path(tmp)
            gz_path, sha256, downloaded_md5, last_modified = download_dump(
                dump_url, tmp_dir, user_agent=user_agent,
                cancel_check=_cancel_pending,
            )
            if downloaded_md5 != md5:
                raise RuntimeError(
                    "downloaded dump failed its MD5 check "
                    "(release changed mid-download?)"
                )
            if _cancel_pending():
                raise ImportCancelled
            dump_path = _decompress(gz_path, tmp_dir)
            load_dump(
                db_path,
                dump_path,
                source_url=dump_url,
                dump_sha256=sha256,
                upstream_md5=md5,
                version=_release_date(last_modified),
            )
        record_check(db_path, status="completed")
        return "completed"
    except ImportCancelled:
        record_check(
            db_path, status="cancelled", detail="stopped by administrator"
        )
        return "cancelled"
    except Exception as exc:  # the loop must survive anything
        record_check(db_path, status="failed", detail=str(exc)[:500])
        return "failed"
    finally:
        _import_running.clear()
        _import_lock.release()


def clear_stale_check(db_path: Path) -> None:
    """A persisted in-progress status can only come from a previous
    process killed mid-check (a restart during the download). It reads
    as failed so the page never shows a phantom running import; the
    last-checked timestamp keeps the interval backoff, and the admin
    button recovers immediately."""
    if not db_path.exists():
        return
    con = sqlite3.connect(db_path, isolation_level=None)
    try:
        try:
            row = con.execute(
                f"SELECT check_status FROM {META_TABLE} WHERE id = 1"
            ).fetchone()
        except sqlite3.OperationalError:
            return
        if row is not None and row[0] == "in-progress":
            con.execute(
                f"UPDATE {META_TABLE} SET check_status = 'failed', "
                "check_detail = 'interrupted by a restart' WHERE id = 1"
            )
    finally:
        con.close()


async def sde_check_loop(settings) -> None:
    """Background SDE check: poll hourly, run the check at most once per
    configured interval (persisted gate — restarts don't reset it). The
    loop only MAINTAINS an existing mirror: a fresh deployment waits for
    the administrator's initial import (Import now or the CLI), and a
    paused system skips checks entirely. A changed MD5 triggers the full
    drop-and-reimport in a worker thread so the event loop never blocks
    on the download."""
    db_path = resolve_db_path(settings.database_url)
    clear_stale_check(db_path)
    while True:
        try:
            if (
                import_exists(db_path)
                and not is_paused(db_path)
                and check_due(db_path, settings.sde_check_interval_hours)
            ):
                status = await asyncio.to_thread(
                    check_and_import,
                    db_path,
                    dump_url=settings.sde_dump_url,
                    user_agent=settings.esi_user_agent,
                )
                logger.info("SDE check: %s", status)
        except Exception:
            logger.exception("SDE check tick failed")
        await asyncio.sleep(CHECK_POLL_SECONDS)


def _run_import(args: argparse.Namespace) -> int:
    settings = get_settings()
    db_path = resolve_db_path(settings.database_url)

    with tempfile.TemporaryDirectory(prefix="sde-import-") as tmp:
        tmp_dir = Path(tmp)
        version = None
        if args.file:
            dump_path = Path(args.file)
            source_url, sha256, upstream_md5 = str(dump_path), None, None
            if not dump_path.exists():
                raise SystemExit(f"No such dump file: {dump_path}")
        else:
            url = args.url or settings.sde_dump_url
            # Change detection first: the published .md5sum costs one tiny
            # request; an unchanged hash means the latest release is
            # already loaded.
            upstream_md5 = fetch_upstream_md5(url, user_agent=settings.esi_user_agent)
            if not args.force and is_current(db_path, upstream_md5):
                meta, _ = sde_info(db_path)
                print(f"Already up to date (release {meta['version'] or 'unknown'}, "
                      "imported "
                      f"{meta['imported_at']}) — use --force to re-import.")
                return 0
            print(f"downloading {url} …")
            gz_path, sha256, md5, last_modified = download_dump(
                url, tmp_dir, user_agent=settings.esi_user_agent
            )
            if upstream_md5 is not None and md5 != upstream_md5:
                raise SystemExit(
                    "Downloaded dump failed its MD5 check — the release "
                    "may have changed mid-download. Try again."
                )
            version = _release_date(last_modified)
            print(f"downloaded ({gz_path.stat().st_size >> 20} MiB, "
                  f"release {version or 'unknown date'}) — decompressing …")
            dump_path = _decompress(gz_path, tmp_dir)
            source_url = url

        print(f"loading into {db_path} …")
        counts = load_dump(
            db_path, dump_path, source_url=source_url, dump_sha256=sha256,
            upstream_md5=upstream_md5, version=version,
        )
    for table, count in counts.items():
        print(f"  {table}: {count:,}")
    print("done.")
    return 0


def _run_info(_args: argparse.Namespace) -> int:
    db_path = resolve_db_path(get_settings().database_url)
    meta, counts = sde_info(db_path)
    if meta is None:
        print("No SDE data imported yet — run `python -m app.sde import`.")
        return 1
    print(f"version:    {meta['version'] or 'unknown'}")
    print(f"source:     {meta['source_url']}")
    print(f"sha256:     {meta['dump_sha256'] or 'n/a (local file)'}")
    print(f"imported:   {meta['imported_at']}")
    for table, count in counts.items():
        print(f"  {table}: {count:,}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.sde",
        description="Import EVE SDE recipe data into the sde_* tables.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    p_import = sub.add_parser("import", help="download and load the SDE")
    p_import.add_argument(
        "--url", default=None, help="dump URL (default: settings.sde_dump_url)"
    )
    p_import.add_argument(
        "--file", default=None, help="load a local SDE SQLite file instead"
    )
    p_import.add_argument(
        "--force", action="store_true",
        help="re-import even when the published MD5 is unchanged",
    )
    sub.add_parser("info", help="show the loaded SDE set")
    args = parser.parse_args(argv)

    if args.command == "import":
        return _run_import(args)
    return _run_info(args)


if __name__ == "__main__":
    raise SystemExit(main())
