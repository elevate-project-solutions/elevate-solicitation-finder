"""Extracts normalized solicitation fields from ESBD CSV rows."""

from datetime import datetime
from typing import Any

from app.collectors.base import CollectedSolicitation
from app.utils.timestamps import normalize_esbd_timestamp

REQUIRED_COLUMNS = {
    "Name",
    "Solicitation ID",
    "Due Date",
    "Due Time",
    "Agency/Texas SmartBuy Member Number",
    "Status",
    "Posting Date",
    "Created",
    "Last Modified",
    "NIGP Codes",
}

DATE_FORMATS = (
    "%m/%d/%Y %I:%M:%S %p",
    "%m/%d/%Y %I:%M %p",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M",
    "%m/%d/%Y",
)

def parse_esbd_datetime(
        date_value: str,
        time_value: str = "",
) -> datetime | None:
    """Parses an ESBD date and optional time."""
    date_value = date_value.strip()
    time_value = time_value.strip()

    if not date_value:
        return None

    value = (
        f"{date_value} {time_value}"
        if time_value
        else date_value
    )

    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(value, date_format)
        except ValueError:
            continue

    raise ValueError(f"Invalid ESBD date/time: {value}")

def extract_esbd_solicitation(
        row: dict[str, Any],
        row_number: int,
) -> CollectedSolicitation:
    """Normalizes one ESBD CSV row into a solicitation."""

    title = str(row.get("Name") or "").strip()
    solicitation_number = str(
        row.get("Solicitation ID") or ""
    ).strip()
    agency_number = str(
        row.get("Agency/Texas SmartBuy Member Number") or ""
    ).strip()

    if not title or not solicitation_number or not agency_number:
        raise ValueError(
            f"Missing required data on row {row_number}."
        )

    due_at = parse_esbd_datetime(
        str(row.get("Due Date") or ""),
        str(row.get("Due Time") or ""),
    )

    posting_at = parse_esbd_datetime(
        str(row.get("Posting Date") or "")
    )

    created_at = parse_esbd_datetime(
        str(row.get("Created") or "")
    )

    modified_at = parse_esbd_datetime(
        str(row.get("Last Modified") or "")
    )

    due_at_utc = normalize_esbd_timestamp(due_at)
    posting_at_utc = normalize_esbd_timestamp(posting_at)
    created_at_utc = normalize_esbd_timestamp(created_at)
    modified_at_utc = normalize_esbd_timestamp(modified_at)

    nigp_codes = [
        code.strip()
        for code in str(row.get("NIGP Codes") or "").split(";")
        if code.strip()
    ]

    normalized_data = {
        **row,
        "agency_member_number": agency_number,
        "posting_at": posting_at_utc.isoformat() if posting_at_utc else None,
        "created_at": created_at_utc.isoformat() if created_at_utc else None,
        "modified_at": modified_at_utc.isoformat() if modified_at_utc else None,
        "nigp_codes": nigp_codes,
    }

    # CSV does not contain agency name, just agency number
    # CSV lacks solicitation URL
    return CollectedSolicitation(
        source_record_id=(
            f"{agency_number}:{solicitation_number}"
        ),
        title=title,
        agency_name=None,
        solicitation_number=solicitation_number,
        source_url=None,
        due_at=due_at_utc,
        status=str(row.get("Status") or "").strip() or None,
        raw_data=normalized_data,
    )