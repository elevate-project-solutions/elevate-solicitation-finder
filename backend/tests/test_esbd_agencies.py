import pytest

from app.collectors import esbd_agencies

@pytest.fixture
def agency_directory(tmp_path, monkeypatch):
    directory = tmp_path / "agencies.csv"

    directory.write_text(
        "agency_number,agency_name\n"
        "601,Texas Department of Transportation\n"
        "S0001,Example School District\n"
        "001,Example State Agency\n",
        encoding="utf-8"
    )

    monkeypatch.setattr(
        esbd_agencies,
        "AGENCY_DIRECTORY",
        directory
    )

    esbd_agencies.load_agency_directory.cache_clear()

    yield directory

    esbd_agencies.load_agency_directory.cache_clear()

def test_resolves_state_agency(agency_directory):
    assert(
        esbd_agencies.resolve_agency_name("601")
        == "Texas Department of Transportation"
    )

def test_resolves_member_number(agency_directory):
    assert(
        esbd_agencies.resolve_agency_name("S0001")
        == "Example School District"
    )

def test_normalizes_member_number(agency_directory):
    assert (
        esbd_agencies.resolve_agency_name(" s0001 ")
        == "Example School District"
    )

def test_preserves_leading_zeros(agency_directory):
    assert (
        esbd_agencies.resolve_agency_name("001")
        == "Example State Agency"
    )

def test_unknown_agency(agency_directory):
    assert (
        esbd_agencies.resolve_agency_name("UNKNOWN")
        is None
    )

def test_missing_agency_number(agency_directory):
    assert (
        esbd_agencies.resolve_agency_name(None)
        is None
    )

def test_missing_directory(agency_directory):
    agency_directory.unlink()

    assert (
        esbd_agencies.resolve_agency_name("601")
        is None
    )