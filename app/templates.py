"""Jinja2 template rendering."""

from pathlib import Path

from fastapi.templating import Jinja2Templates

_package_dir = Path(__file__).parent
templates = Jinja2Templates(directory=str(_package_dir / "templates"))


def portrait_url(character_id: int, size: int = 64) -> str:
    """Public character portrait — no API call required."""
    return f"https://images.evetech.net/characters/{character_id}/portrait?size={size}"
