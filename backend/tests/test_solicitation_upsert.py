from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.collectors.base import CollectedSolicitation
from app.services.solicitation_upsert import (
    save_or_update_solicitations,
)

DUE_AT = datetime(2026, 12, 20, 21, 0, tzinfo=timezone.utc)

def make_solicitation(
        record_id="719:RFP-123",
        title="Roof Replacement",
        due_at=DUE_AT,
):
    return CollectedSolicitation(
        source_record_id=record_id,
        title=title,
        agency_name=None,
        solicitation_number="RFP-123",
        source_url=None,
        due_at=due_at,
        status="Posted",
        raw_data={},
    )

def make_session(existing=None):
    session = MagicMock()
    session.execute.return_value.scalar_one_or_none.return_value = existing
    return session

def test_inserts_new_solicitation():
    session = make_session()

    result = save_or_update_solicitations(
        session,
        [make_solicitation()],
        "texas_esbd",
    )

    assert result.inserted == 1
    assert result.updated == 0

    session.add.assert_called_once()

    record = session.add.call_args.args[0]

    assert record.source == "texas_esbd"
    assert record.source_record_id == "719:RFP-123"
    assert record.title == "Roof Replacement"
    assert record.due_at == DUE_AT
    assert record.agency is None
    assert record.source_url is None

    session.flush.assert_called_once()
    session.commit.assert_not_called()

def test_updates_existing_solicitation():
    existing = SimpleNamespace(
        source="texas_esbd",
        source_record_id="719:RFP-123",
        title="Old Roof Title",
        agency=None,
        solicitation_number="RFP-123",
        source_url=None,
        due_at=DUE_AT,
        status="Posted",
        first_seen_at=datetime(
            2026, 10, 1, tzinfo=timezone.utc
        ),
        last_seen_at=None,
        updated_at=None,
    )

    original_first_seen = existing.first_seen_at
    session = make_session(existing)

    result = save_or_update_solicitations(
        session,
        [make_solicitation(title="Updated Roof Title")],
        "texas_esbd",
    )

    assert result.inserted == 0
    assert result.updated == 1
    assert existing.title == "Updated Roof Title"
    assert existing.first_seen_at == original_first_seen
    assert existing.last_seen_at is not None
    assert existing.updated_at is not None

    session.add.assert_not_called()
    session.flush.assert_called_once()

def test_empty_collection():
    session = make_session()

    result = save_or_update_solicitations(
        session,
        [],
        "texas_esbd",
    )

    assert result.inserted == 0
    assert result.updated == 0

    session.add.assert_not_called()

def test_missing_record_id_is_rejected():
    session = make_session()

    with pytest.raises(ValueError, match="source_record_id"):
        save_or_update_solicitations(
            session,
            [make_solicitation(record_id="")],
            "texas_esbd",
        )

    session.add.assert_not_called()

def test_missing_source_name_is_rejected():
    session = make_session()

    with pytest.raises(ValueError, match="source_name"):
        save_or_update_solicitations(
            session,
            [make_solicitation()],
            "",
        )

def test_naive_deadline_is_rejected():
    session = make_session()

    with pytest.raises(ValueError, match="timezone-aware"):
        save_or_update_solicitations(
            session,
            [
                make_solicitation(
                    due_at=datetime(2026, 12, 20, 15, 0)
                )
            ],
            "texas_esbd",
        )

    session.add.assert_not_called()

def test_missing_deadline_is_allowed():
    session = make_session()

    result = save_or_update_solicitations(
        session,
        [make_solicitation(due_at=None)],
        "texas_esbd",
    )

    assert result.inserted == 1
    record = session.add.call_args.args[0]
    assert record.due_at is None