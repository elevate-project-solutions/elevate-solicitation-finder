import uuid

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.db.session import database_url
from app.models import (
    SolicitationDuplicateCandidate,
    SolicitationExternalRef,
    SolicitationSource,
)
from app.services.solicitation_deduplication import (
    import_solicitation,
)

@pytest.fixture
def db():
    """
    Every test uses a database transaction that rolls back
    """

    engine = create_engine(database_url)

    with engine.connect() as connection:
        transaction = connection.begin()

        try:
            with Session(bind=connection) as session:
                yield session
        finally:
            transaction.rollback()

    engine.dispose()

@pytest.fixture
def source(db):
    key = "test_" + uuid.uuid4().hex

    item = SolicitationSource(
        name="Test Procurement Portal",
        source_key=key,
        base_url="https://example.test",
    )

    db.add(item)
    db.flush()

    return item

def sample(source, suffix="001", **overrides):
    data = {
        "source_key": source.source_key,
        "agency": "Test City",
        "title": "Roof Replacement",
        "solicitation_number": "TEST-2026-001",
        "source_url": f"https://example.test/canonical/{suffix}",
        "external_url": f"https://example.test/bids/{suffix}",
        "external_id": f"external-{suffix}",
    }
    data.update(overrides)
    return data

def test_first_import_creates_solicitation(db,source):
    result = import_solicitation(
        db, **sample(source)
    )

    assert result.outcome == "created"
    assert result.solicitation_id is not None

def test_second_import_reuses_existing_record(db,source):
    data = sample(source)

    first = import_solicitation(db, **data)
    second = import_solicitation(db, **data)

    assert first.solicitation_id == second.solicitation_id
    assert second.outcome == "existing"

    refs = db.scalar(
        select(func.count())
        .select_from(SolicitationExternalRef)
        .where(
            SolicitationExternalRef.solicitation_id == first.solicitation_id
        )
    )

    assert refs == 1

def test_same_agency_and_number_requires_review(db, source):
    first = import_solicitation(db, **sample(source, "001"))
    second = import_solicitation(db, **sample(source, "002"))

    assert second.outcome == "review_required"
    assert first.solicitation_id != second.solicitation_id

    candidate = db.scalar(
        select(SolicitationDuplicateCandidate).where(
            SolicitationDuplicateCandidate.solicitation_id_1 == min(first.solicitation_id, second.solicitation_id),
            SolicitationDuplicateCandidate.solicitation_id_2 == max(first.solicitation_id, second.solicitation_id),
        )
    )

    assert candidate is not None
    assert candidate.review_status == "pending"

def test_conflicting_external_id_is_rejected(db, source):
    import_solicitation(db, **sample(source, "001"))

    with pytest.raises(ValueError, match="Identifier conflict"):
        import_solicitation(
            db,
            **sample(
                source,
                "002",
                external_id="external-001",
            ),
        )

def test_existing_canonical_url_is_reused(db, source):
    first = import_solicitation(
        db, **sample(source, "001")
    )
    second = import_solicitation(
        db, **sample(
            source, 
            "002", 
            source_url="https://example.test/canonical/001"
        ),
    )

    assert second.outcome == "existing_url"
    assert second.solicitation_id == first.solicitation_id

def test_different_agencies_do_not_auto_merge(db, source):
    first = import_solicitation(
        db, **sample(source, "001")
    )

    second = import_solicitation(
        db,
        **sample(
            source,
            "002",
            agency="Another City",
        ),
    )

    assert second.outcome == "created"
    assert second.solicitation_id != first.solicitation_id