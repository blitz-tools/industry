"""Jinja2 template rendering."""

import hashlib
from pathlib import Path

from fastapi.templating import Jinja2Templates

_package_dir = Path(__file__).parent
templates = Jinja2Templates(directory=str(_package_dir / "templates"))


def portrait_url(character_id: int, size: int = 64) -> str:
    """Public character portrait — no API call required."""
    return f"https://images.evetech.net/characters/{character_id}/portrait?size={size}"


def corporation_logo_url(corporation_id: int, size: int = 64) -> str:
    """Public corporation logo — no API call required."""
    return f"https://images.evetech.net/corporations/{corporation_id}/logo?size={size}"


def type_icon_url(type_id: int, size: int = 32, kind: str = "icon") -> str:
    """Public type icon — no API call required. `kind` is the imageserver
    path segment: "icon" for regular types, but blueprints need their
    dedicated renders ("bp" originals, "bpc" copies) — the plain icon
    endpoint 400s on blueprint types."""
    return f"https://images.evetech.net/types/{type_id}/{kind}?size={size}"


# Image render URLs are usable directly from templates.
templates.env.globals["portrait_url"] = portrait_url
templates.env.globals["corporation_logo_url"] = corporation_logo_url
templates.env.globals["type_icon_url"] = type_icon_url


def format_duration(seconds: int) -> str:
    """Seconds → the mockup's compact duration form (h / d)."""
    if seconds <= 0:
        return "—"
    hours = seconds / 3600
    if hours < 1:
        return f"{seconds}s"
    if hours < 48:
        value = f"{hours:.1f}".rstrip("0").rstrip(".")
        return f"{value} h"
    days = hours / 24
    value = f"{days:.1f}".rstrip("0").rstrip(".")
    return f"{value} d"


def format_isk(value: float | None) -> str:
    return "—" if value is None else f"{value:,.2f} Ƶ"


def format_qty(value: int | None) -> str:
    return "—" if value is None else f"{value:,}"


# Shared display formatters (the planner and plans pages).
templates.env.globals["format_duration"] = format_duration
templates.env.globals["format_isk"] = format_isk
templates.env.globals["format_qty"] = format_qty


def _static_version() -> str:
    """Cache-buster for /static assets: the newest file mtime, so edited
    stylesheets and scripts reload instead of serving from browser cache."""
    static_dir = _package_dir / "static"
    newest = max(path.stat().st_mtime for path in static_dir.iterdir() if path.is_file())
    return str(int(newest))


class _LazyStaticVersion:
    """Evaluates the cache-buster at render time, not import time: a
    stylesheet edited after the process started still gets a fresh ?v=
    (the startup-time value served a stale URL and browsers kept the
    cached file — the changes were on disk but never fetched)."""

    def __str__(self) -> str:
        return _static_version()


templates.env.globals["static_version"] = _LazyStaticVersion()


def dev_site_version() -> str:
    """Change token over the code, template, and static trees — the dev
    auto-refresh poller compares it (see DEV_AUTO_RELOAD and
    static/dev-reload.js). Called per render so template-only edits (no
    process restart) still change it."""
    entries = []
    for path in sorted(_package_dir.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        try:
            entries.append((str(path), path.stat().st_mtime_ns))
        except OSError:
            continue  # file vanished mid-walk
    return hashlib.sha1(repr(entries).encode()).hexdigest()[:16]


templates.env.globals["dev_site_version"] = dev_site_version
