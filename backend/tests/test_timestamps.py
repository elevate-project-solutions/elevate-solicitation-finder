from datetime import datetime, timezone

import pytest

from app.utils.timestamps import normalize_esbd_timestamp


def test_standard_time():
    result = normalize_esbd_timestamp(datetime(2026, 1, 15, 15, 0))
    assert result == datetime(2026, 1, 15, 21, 0, tzinfo=timezone.utc)

def test_daylight_time():
    result = normalize_esbd_timestamp(datetime(2026, 7, 15, 15, 0))
    assert result == datetime(2026, 7, 15, 20, 0, tzinfo=timezone.utc)

def test_none_timestamp():
    assert normalize_esbd_timestamp(None) is None

def test_aware_timestamp():
    value = datetime(2026, 7, 15, 20, 0, tzinfo=timezone.utc)
    assert normalize_esbd_timestamp(value) == value

def test_nonexistent_spring_time():
    with pytest.raises(ValueError, match="Nonexistent"):
        normalize_esbd_timestamp(datetime(2026, 3, 8, 2, 30))

def test_ambigous_fall_time():
    with pytest.raises(ValueError, match="Ambiguous"):
        normalize_esbd_timestamp(datetime(2026, 11, 1, 1, 30))