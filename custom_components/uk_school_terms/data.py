"""Bundled council data loading."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from .model import CouncilData, CouncilDataError, validate_council_data

DATA_DIRECTORY = Path(__file__).parent / "data"


def list_councils(country: str) -> dict[str, str]:
    """Return authority IDs mapped to display names."""
    country_directory = DATA_DIRECTORY / country
    if not country_directory.is_dir():
        return {}
    councils: dict[str, str] = {}
    for path in sorted(country_directory.glob("*.yaml")):
        council = load_council(country, path.stem)
        councils[council.authority] = council.name
    return councils


@lru_cache(maxsize=32)
def load_council(country: str, authority: str) -> CouncilData:
    """Load and validate one bundled council file."""
    path = DATA_DIRECTORY / country / f"{authority}.yaml"
    if not path.is_file() or path.parent != DATA_DIRECTORY / country:
        raise CouncilDataError(f"Unknown council: {country}/{authority}")
    with path.open(encoding="utf-8") as council_file:
        raw = yaml.load(council_file, Loader=yaml.BaseLoader)
    council = validate_council_data(raw)
    if council.country != country or council.authority != authority:
        raise CouncilDataError("Council file path does not match its metadata")
    return council

