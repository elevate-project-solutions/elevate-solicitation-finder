from datetime import datetime, timedelta, timezone

import pytest

from app.filters.deadlines import (
    filter_solicitations_by_deadline,
    meets_deadline_requirement,
)

FIXED_NOW = datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc)

@pytest.mark.parametrize(
    ("days_until_due", "expected"),
    [
        (45, True),
        (31, True),
        (30, True),
        (29, False),
        (1, False),
        (-1, False),
    ],
)
def test_default_deadline_rule(days_until_due, expected):
    due_at = FIXED_NOW + timedelta(days=days_until_due)

    assert meets_deadline_requirement(
        due_at=due_at,
        now=FIXED_NOW,
    ) is expected

def test_missing_deadline_is_excluded():
    assert meets_deadline_requirement(
        due_at=None,
        now=FIXED_NOW,
    ) is False

def test_custom_minimum_days():
    due_at = FIXED_NOW + timedelta(days=20)

    assert meets_deadline_requirement(
        due_at=due_at,
        minimum_days=14,
        now=FIXED_NOW,
    ) is True

    assert meets_deadline_requirement(
        due_at=due_at,
        minimum_days=30,
        now=FIXED_NOW,
    ) is False

def test_negative_minimum_days_is_rejected():
    with pytest.raises(ValueError, match="cannot be negative"):
        meets_deadline_requirement(
            due_at=FIXED_NOW,
            minimum_days=-1,
            now=FIXED_NOW,
        )

def test_naive_deadline_is_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        meets_deadline_requirement(
            due_at=datetime(2026, 12, 15, 12, 0),
            now=FIXED_NOW,
        )

def test_naive_now_is_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        meets_deadline_requirement(
            due_at=FIXED_NOW + timedelta(days=45),
            now=datetime(2026, 11, 2, 12, 0),
        )

def test_exact_boundary_includes_deadline():
    due_at = FIXED_NOW + timedelta(days=30)

    assert meets_deadline_requirement(
        due_at=due_at,
        now=FIXED_NOW,
    ) is True

def test_one_second_before_boundary_is_excluded():
    due_at = FIXED_NOW + timedelta(days=30) - timedelta(seconds=1)

    assert meets_deadline_requirement(
        due_at=due_at,
        now=FIXED_NOW,
    ) is False

def test_filter_preserves_eligible_records():
    from app.collectors.base import CollectedSolicitation

    def make_record(number, days):
        return CollectedSolicitation(
            source_record_id=number,
            title=f"Solicitation {number}",
            agency_name=None,
            solicitation_number=number,
            source_url=None,
            due_at=FIXED_NOW + timedelta(days=days),
            status="Posted",
            raw_data={},
        )

    eligible = make_record("A", 45)
    ineligible = make_record("B", 10)
    records = [eligible, ineligible]

    filtered = filter_solicitations_by_deadline(
        records,
        minimum_days=30,
        now=FIXED_NOW,
    )

    assert filtered == [eligible]
    assert len(records) == 2

def test_negative_minimum_rejected_for_empty_collection():
    with pytest.raises(ValueError, match="cannot be negative"):
        filter_solicitations_by_deadline(
            [],
            minimum_days=-1,
            now=FIXED_NOW,
        )