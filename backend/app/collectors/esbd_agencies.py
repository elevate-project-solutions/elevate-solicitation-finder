"""Resolves Texas ESBD agency and member numbers"""

import csv
import logging
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

AGENCY_DIRECTORY = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "esbd_agencies.csv"
)

@lru_cache(maxsize=1)
def load_agency_directory() -> dict[str, str]:
    """Loads the local agency reference directory"""

    agencies: dict[str, str] = {}

    if not AGENCY_DIRECTORY.exists():
        logger.warning(
            "ESBD agency directory not found: %s",
            AGENCY_DIRECTORY,
        )
        return agencies

    with AGENCY_DIRECTORY.open(
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        required = {"agency_number", "agency_name"}

        if not required.issubset(reader.fieldnames or []):
            raise ValueError(
                "ESBD agency directory has invalid columns."
            )

        for row in reader:
            number = (
                row.get("agency_number") or ""
            ).strip().upper()

            name = (
                row.get("agency_name") or ""
            ).strip()

            if number and name:
                agencies[number] = name

    return agencies

def resolve_agency_name(
        agency_number: str | None,
) -> str | None:
    """Returns the agency name for a known member number."""

    if not agency_number:
        return None

    normalized_number = agency_number.strip().upper()

    return load_agency_directory().get(normalized_number)