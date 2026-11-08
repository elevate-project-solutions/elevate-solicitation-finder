import uuid
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.collectors.base import CollectedSolicitation
from app.db.session import database_url
from app.models import Solicitation, SolicitationDuplicateCandidate
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

@pytest.fixture
def integration_db():
    """Uses PostgreSQL and rolls back changes after each test."""
    engine = create_engine(database_url)

    try:
        with engine.connect() as connection:
            transaction = connection.begin()

            try:
                with Session(bind=connection) as session:
                    yield session
            finally:
                transaction.rollback()
    finally:
        engine.dispose()

@pytest.fixture
def integration_source():
    """Gives each test a unique source name."""
    return f"test_esbd_{uuid.uuid4().hex}"

def make_integration_solicitation(
        *,
        record_id="TEST-001",
        agency="Test City",
        number="RFP-001",
        title="Roof Replacement",
        due_at=None,
):
    if due_at is None:
        due_at = datetime(
            2027, 1, 15, 17, 0,
            tzinfo=timezone.utc,
        )

    return CollectedSolicitation(
        source_record_id=record_id,
        title=title,
        agency_name=agency,
        solicitation_number=number,
        source_url=None,
        due_at=due_at,
        status="Posted",
        raw_data={},
    )

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

def test_reimport_updates_existing_record(
        integration_db,
        integration_source,
):
    """Checking if reimporting the same ID updates instead of inserting."""

    first = make_integration_solicitation(
        title="Original Roof Replacement",
    )

    second = make_integration_solicitation(
        title = "Updated Roof Replacement",
    )

    first_result = save_or_update_solicitations(
        integration_db,
        [first],
        integration_source,
    )

    second_result = save_or_update_solicitations(
        integration_db,
        [second],
        integration_source,
    )

    assert first_result.inserted == 1
    assert second_result.inserted == 0
    assert second_result.updated == 1

    records = integration_db.scalars(
        select(Solicitation).where(
            Solicitation.source == integration_source
        )
    ).all()

    assert len(records) == 1
    assert records[0].title == "Updated Roof Replacement"

def test_different_ids_create_duplicate_candidate(
        integration_db,
        integration_source,
):
    """Checks that matching agency and number triggers review"""

    first = make_integration_solicitation(
        record_id="TEST-001",
    )

    second = make_integration_solicitation(
        record_id="TEST-002",
    )

    save_or_update_solicitations(
        integration_db,
        [first, second],
        integration_source
    )

    records = integration_db.scalars(
        select(Solicitation).where(
            Solicitation.source == integration_source
        )
    ).all()

    assert len(records) == 2

    ids = {record.id for record in records}

    candidates = integration_db.scalars(
        select(SolicitationDuplicateCandidate).where(
            SolicitationDuplicateCandidate.solicitation_id_1.in_(ids),
            SolicitationDuplicateCandidate.solicitation_id_2.in_(ids)
        )
    ).all()

    assert len(candidates) == 1
    assert candidates[0].review_status == "pending"

def test_different_agencies_are_not_duplicates(
        integration_db,
        integration_source,
):
    """Checks that same solicitation number at different agencies is allowed"""

    first = make_integration_solicitation(
        record_id="TEST-001",
        agency="City of Dallas",
    )

    second = make_integration_solicitation(
        record_id="TEST-002",
        agency="City of Austin",
    )

    save_or_update_solicitations(
        integration_db,
        [first, second],
        integration_source,
    )

    records = integration_db.scalars(
        select(Solicitation).where(
            Solicitation.source == integration_source
        )
    ).all()

    assert len(records) == 2

    ids = {record.id for record in records}

    candidates = integration_db.scalars(
        select(SolicitationDuplicateCandidate).where(
            SolicitationDuplicateCandidate.solicitation_id_1.in_(ids),
            SolicitationDuplicateCandidate.solicitation_id_2.in_(ids),
        )
    ).all()

    assert len(candidates) == 0

def test_missing_agency_skips_duplicate_detection(
        integration_db,
        integration_source,
):
    """Checks that missing agency info will not cause automatic matches"""

    first = make_integration_solicitation(
        record_id="TEST-001",
        agency=None,
    )

    second = make_integration_solicitation(
        record_id="TEST-002",
        agency=None,
    )

    save_or_update_solicitations(
        integration_db,
        [first, second],
        integration_source,
    )

    records = integration_db.scalars(
        select(Solicitation).where(
            Solicitation.source == integration_source
        )
    ).all()

    assert len(records) == 2

    ids = {record.id for record in records}

    candidates = integration_db.scalars(
        select(SolicitationDuplicateCandidate).where(
            SolicitationDuplicateCandidate.solicitation_id_1.in_(ids),
            SolicitationDuplicateCandidate.solicitation_id_2.in_(ids),
        )
    ).all()

    assert len(candidates) == 0

def test_updated_deadline_replaces_old_deadline(
        integration_db,
        integration_source,
):
    """Checks if an amended deadline updates the existing record"""

    original_deadline = datetime(
        2027, 1, 15, 17, 0,
        tzinfo=timezone.utc,
    )

    new_deadline = original_deadline + timedelta(days=7)

    first = make_integration_solicitation(
        due_at=original_deadline,
    )

    second = make_integration_solicitation(
        due_at=new_deadline,
    )

    save_or_update_solicitations(
        integration_db,
        [first],
        integration_source,
    )

    result = save_or_update_solicitations(
        integration_db,
        [second],
        integration_source,
    )

    record = integration_db.scalar(
        select(Solicitation).where(
            Solicitation.source == integration_source,
            Solicitation.source_record_id == "TEST-001",
        )
    )

    assert result.updated == 1
    assert record.due_at == new_deadline

def test_reimport_does_not_duplicate_candidates(
        integration_db,
        integration_source,
):
    """Checks that repeated imports does not create extra review entries"""

    first = make_integration_solicitation(
        record_id="TEST-001",
    )

    second = make_integration_solicitation(
        record_id="TEST-002",
    )

    save_or_update_solicitations(
        integration_db,
        [first, second],
        integration_source,
    )

    save_or_update_solicitations(
        integration_db,
        [first, second],
        integration_source,
    )

    records = integration_db.scalars(
        select(Solicitation).where(
            Solicitation.source == integration_source
        )
    ).all()

    assert len(records) == 2

    ids = {record.id for record in records}

    candidate_count = integration_db.scalar(
        select(func.count())
        .select_from(SolicitationDuplicateCandidate)
        .where(
            SolicitationDuplicateCandidate.solicitation_id_1.in_(ids),
            SolicitationDuplicateCandidate.solicitation_id_2.in_(ids),
        )
    )

    assert candidate_count == 1