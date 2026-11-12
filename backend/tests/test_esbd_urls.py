import pytest

from app.collectors.esbd_urls import build_esbd_url

def test_builds_official_esbd_url():
    assert build_esbd_url("27-0011101") == (
        "https://www.txsmartbuy.gov/esbd/27-0011101"
    )

def test_strips_whitespace():
    assert build_esbd_url(" 123-ABC ") == (
        "https://www.txsmartbuy.gov/esbd/123-ABC"
    )

def test_encodes_special_characters():
    assert build_esbd_url("ABC/123") == (
        "https://www.txsmartbuy.gov/esbd/ABC%2F123"
    )

def test_rejects_empty_id():
    with pytest.raises(ValueError):
        build_esbd_url(" ")