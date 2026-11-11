import csv
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

import pytest

from app.collectors.esbd import ESBDCollector

FIXTURES = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "esbd"
)

CSV_PATH = FIXTURES / "verified_export.csv"
JSON_PATH = FIXTURES / "verified_listings.json"

REQUIRED_VERIFIED_FIELDS = (
    "title",
    "solicitation_number",
    "agency_member_number",
    "due_date",
    "due_time",
    "status",
)

def load_csv_rows():
    with CSV_PATH.open(
        encoding="utf-8-sig",
        newline="",
    ) as file:
        return list(csv.DictReader(file))

def load_verified_rows():
    with JSON_PATH.open(encoding="utf-8") as file:
        return json.load(file)

def normalize_text(value):
    if value is None:
        return None

    return " ".join(str(value).split()).casefold()

def normalize_date(value):
    if not value:
        return None

    value = str(value).strip()

    for date_format in (
        "%m/%d/%Y",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(
                value, date_format
            ).date().isoformat()
        except ValueError:
            continue

    raise ValueError(f"Unknown date format: {value}")

def normalize_time(value):
    if not value:
        return None

    value = str(value).strip()

    for time_format in (
        "%I:%M %p",
        "%H:%M",
        "%H:%M:%S",
    ):
        try:
            return datetime.strptime(
                value, time_format
            ).strftime("%H:%M")
        except ValueError:
            continue

    raise ValueError(f"Unknown time format: {value}")

def collected_by_id():
    collection = ESBDCollector(
        csv_path=CSV_PATH
    ).run()

    records = collection.solicitations

    ids = [
        record.source_record_id
        for record in records
    ]

    assert len(ids) == len(set(ids)), (
        "Collector returned duplicate source IDs"
    )

    return {
        record.source_record_id: record
        for record in records
    }

def expected_source_id(row):
    agency_number = row[
        "Agency/Texas SmartBuy Member Number"
    ].strip()

    solicitation_id = row[
        "Solicitation ID"
    ].strip()

    return f"{agency_number}:{solicitation_id}"

def test_ground_truth_is_complete():
    verified = load_verified_rows()

    assert len(verified) == 10

    ids = [
        record["source_record_id"]
        for record in verified
    ]

    assert len(ids) == len(set(ids))

    for record in verified:
        assert record["verified"] is True, (
            f"{record['source_record_id']} "
            "has not been manually verified"
        )

        assert record["official_url"], (
            f"Missing official URL for "
            f"{record["source_record_id"]}"
        )

        for field in REQUIRED_VERIFIED_FIELDS:
            assert record[field] is not None, (
                f"Missing verified {field} for "
                f"{record['source_record_id']}"
            )

def test_csv_contains_exactly_ten_records():
    rows = load_csv_rows()

    assert len(rows) == 10

    ids = [
        row["Solicitation ID"].strip()
        for row in rows
    ]

    assert len(ids) == len(set(ids))

def test_csv_matches_ground_truth():
    """
    Confirms that verified ESBD listings correspond to
    record in the historical CSV export.
    
    Historical field differences are documented in
    validation_report.csv rather than treated as
    collector failures
    """
    csv_rows = {
        row["Solicitation ID"].strip(): row
        for row in load_csv_rows()
    }

    verified_rows = load_verified_rows()

    assert len(csv_rows) == len(verified_rows)

    for expected in verified_rows:
        record_id = expected["source_record_id"]

        assert record_id in csv_rows, (
            f"Verified solicitation missing from "
            f"CSV: {record_id}"
        )

        assert expected["verified"] is True, (
            f"Solicitation not verified: {record_id}"
        )

        assert expected["official_url"], (
            f"Missing official ESBD URL: {record_id}"
        )

        actual = csv_rows[record_id]

        assert normalize_text(
            actual["Solicitation ID"]
        ) == normalize_text(
            expected["solicitation_number"]
        ), f"Solicitation number mismatch: {record_id}"

        assert normalize_text(
            actual[
                "Agency/Texas SmartBuy Member Number"
            ]
        ) == normalize_text(
            expected["agency_member_number"]
        ), f"Agency member mismatch: {record_id}"

def test_collector_preserves_source_records():
    actual = collected_by_id()

    expected_ids = {
        expected_source_id(row)
        for row in load_csv_rows()
    }

    assert set(actual) == expected_ids, (
        "Collector IDs differ from source CSV IDs"
    )

def test_collector_preserves_titles():
    actual = collected_by_id()

    for row in load_csv_rows():
        record_id = expected_source_id(row)

        assert normalize_text(
            actual[record_id].title
        ) == normalize_text(
            row["Name"]
        ), f"Collector title mismatch: {record_id}"

def test_collector_preserves_status():
    actual = collected_by_id()

    for row in load_csv_rows():
        record_id = expected_source_id(row)

        assert normalize_text(
            actual[record_id].status
        ) == normalize_text(
            row["Status"]
        ), f"Collector status mismatch: {record_id}"

def test_collector_preserves_due_dates():
    actual = collected_by_id()

    texas_timezone = ZoneInfo("America/Chicago")

    for row in load_csv_rows():
        record_id = expected_source_id(row)
        due_at = actual[record_id].due_at

        if due_at is None:
            assert not row["Due Date"], (
                f"Missing collector due date: {record_id}"
            )
            continue

        if isinstance(due_at, str):
            due_at = datetime.fromisoformat(due_at)

        assert due_at.tzinfo is not None, (
            f"Deadline has no timezone: {record_id}"
        )

        # Converts the stored instant to TX local time
        local_due_at = due_at.astimezone(
            texas_timezone
        )

        assert local_due_at.date().isoformat() == (
            normalize_date(row["Due Date"])
        ), f"Collector due date mismatch: {record_id}"

        if row["Due Time"]:
            assert local_due_at.strftime("%H:%M") == (
                normalize_time(row["Due Time"])
            ), f"Collector due time mismatch: {record_id}"

def test_collector_is_repeatable():
    first = ESBDCollector(
        csv_path=CSV_PATH
    ).run()

    second = ESBDCollector(
        csv_path=CSV_PATH
    ).run()

    first_records = [
        (
            item.source_record_id,
            item.title,
            item.status,
            item.due_at,
        )
        for item in first.solicitations
    ]

    second_records = [
        (
            item.source_record_id,
            item.title,
            item.status,
            item.due_at,
        )
        for item in second.solicitations
    ]

    assert first_records == second_records