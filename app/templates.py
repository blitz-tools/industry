"""Jinja2 template rendering."""

from pathlib import Path

from fastapi.templating import Jinja2Templates

_package_dir = Path(__file__).parent
templates = Jinja2Templates(directory=str(_package_dir / "templates"))


def portrait_url(character_id: int, size: int = 64) -> str:
    """Public character portrait — no API call required."""
    return f"https://images.evetech.net/characters/{character_id}/portrait?size={size}"


def type_icon_url(type_id: int, size: int = 32, kind: str = "icon") -> str:
    """Public type icon — no API call required. `kind` is the imageserver
    path segment: "icon" for regular types, but blueprints need their
    dedicated renders ("bp" originals, "bpc" copies) — the plain icon
    endpoint 400s on blueprint types."""
    return f"https://images.evetech.net/types/{type_id}/{kind}?size={size}"


# Image render URLs are usable directly from templates.
templates.env.globals["portrait_url"] = portrait_url
templates.env.globals["type_icon_url"] = type_icon_url
