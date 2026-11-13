from datetime import datetime, timezone

import pytest

from app.collectors.esbd_extraction import (
    extract_esbd_solicitation,
    parse_esbd_datetime,
)
from app.utils.timestamps import normalize_esbd_timestamp


@pytest.fixture
def sample_row():
    return {
        "Name": "Roof Replacement",
        "Solicitation ID": "RFP-123",
        "Due Date": "11/12/2026",
        "Due Time": "3:00 PM",
        "Agency/Texas SmartBuy Member Number": "719",
        "Status": "Posted",
        "Posting Date": "10/21/2026",
        "Created": "10/21/2026 5:26 pm",
        "Last Modified": "10/22/2026 9:30 am",
        "NIGP Codes": "91438; 91066;",
    }

def test_extract_solicitation_number(sample_row):
    record = extract_esbd_solicitation(sample_row, 2)

    assert record.solicitation_number == "RFP-123"
    assert record.source_record_id == "719:RFP-123"

def test_extract_title(sample_row):
    record = extract_esbd_solicitation(sample_row, 2)

    assert record.title == "Roof Replacement"

def test_extract_agency_identifier(sample_row):
    record = extract_esbd_solicitation(sample_row, 2)

    assert record.agency_name is None
    assert record.raw_data["agency_member_number"] == "719"

def test_extract_due_date(sample_row):
    record = extract_esbd_solicitation(sample_row, 2)

    assert record.due_at == datetime(
        2026, 11, 12, 21, 0, tzinfo=timezone.utc
    )

def test_extract_posting_date(sample_row):
    record = extract_esbd_solicitation(sample_row, 2)

    expected = normalize_esbd_timestamp(
        parse_esbd_datetime(sample_row["Posting Date"])
    )

    assert record.raw_data["posting_at"] == (
        expected.isoformat() if expected else None
    )

def test_extract_created_date(sample_row):
    record = extract_esbd_solicitation(sample_row, 2)

    expected = normalize_esbd_timestamp(
        parse_esbd_datetime(sample_row["Created"])
    )

    assert record.raw_data["created_at"] == (
        expected.isoformat() if expected else None
    )
    
def test_extract_modified_date(sample_row):
    record = extract_esbd_solicitation(sample_row, 2)

    expected = normalize_esbd_timestamp(
        parse_esbd_datetime(sample_row["Last Modified"])
    )

    assert record.raw_data["modified_at"] == (
        expected.isoformat() if expected else None
    )

def test_esbd_source_url_is_generated(sample_row):
    record = extract_esbd_solicitation(sample_row, 2)

    assert record.source_url == "https://www.txsmartbuy.gov/esbd/RFP-123"

def test_extract_nigp_codes(sample_row):
    record = extract_esbd_solicitation(sample_row, 2)

    assert record.raw_data["nigp_codes"] == [
        "91438",
        "91066",
    ]

def test_missing_required_field(sample_row):
    sample_row["Solicitation ID"] = ""

    with pytest.raises(ValueError, match="row 2"):
        extract_esbd_solicitation(sample_row, 2)

def test_invalid_due_date(sample_row):
    sample_row["Due Date"] = "not-a-date"

    with pytest.raises(ValueError, match="Invalid ESBD"):
        extract_esbd_solicitation(sample_row, 2)

def test_blank_date_returns_none():
    assert parse_esbd_datetime("") is None

def test_parse_24_hour_time():
    result = parse_esbd_datetime(
        "11/12/2026",
        "15:30",
    )

    assert result == datetime(2026, 11, 12, 15, 30)

def test_parse_date_only():
    result = parse_esbd_datetime("11/12/2026")

    assert result == datetime(2026, 11, 12)

def test_original_data_is_preserved(sample_row):
    record = extract_esbd_solicitation(sample_row, 2)

    assert record.raw_data["Name"] == "Roof Replacement"
    assert record.raw_data["Status"] == "Posted"

def test_parse_24_hour_time_with_seconds():
    result = parse_esbd_datetime("8/2/2024", "13:00:00")

    assert result == datetime(2024, 8, 2, 13, 0 ,0)

def test_parse_12_hour_time_with_seconds():
    result = parse_esbd_datetime("4/8/2021", "01:00:00 PM")

    assert result == datetime(2021, 4, 8, 13, 0, 0)
