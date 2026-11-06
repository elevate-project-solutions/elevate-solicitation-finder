import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.collectors.base import CollectedSolicitation
from app.models.solicitation import Solicitation
from app.services.solicitation_upsert import (
    save_or_update_solicitations,
)


def make_record(record_id, title):
    return CollectedSolicitation(
        source_record_id=record_id,
        title=title,
        agency_name=None,
        solicitation_number=record_id,
        source_url=None,
        due_at=datetime(
            2026, 12, 20, 21, 0, tzinfo=timezone.utc
        ),
        status="Posted",
        raw_data={},
    )

@pytest.fixture
def db_session():
    url = os.getenv("TEST_DATABASE_URL")

    if not url:
        pytest.skip("TEST_DATABASE_URL is not configured")

    if url.startswith("postgresql://"):
        url = url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )

    if not url.startswith("postgresql+psycopg://"):
        pytest.fail("TEST_DATABASE_URL must use PostgreSQL")

    development_url = os.getenv("DATABASE_URL")

    def normalize_url(value):
        if value and value.startswith("postgresql://"):
            return value.replace(
                "postgresql://",
                "postgresql+psycopg://",
                1,
            )
        return value

    if normalize_url(development_url) == url:
        pytest.fail(
            "TEST_DATABASE_URL must differ from DATABASE_URL"
        )

    engine = create_engine(url, pool_pre_ping=True)

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

def test_postgres_insert_update_no_duplicates(db_session):
    source_name = f"test_{uuid4().hex}"
    record_id = f"TEST-{uuid4().hex}"

    first = make_record(record_id, "Original Roof Title")

    first_result = save_or_update_solicitations(
        db_session,
        [first],
        source_name,
    )

    assert first_result.inserted == 1
    assert first_result.updated == 0

    updated = make_record(record_id, "Updated Roof Title")

    second_result = save_or_update_solicitations(
        db_session,
        [updated],
        source_name,
    )

    assert second_result.inserted == 0
    assert second_result.updated == 1

    records = db_session.execute(
        select(Solicitation).where(
            Solicitation.source == source_name,
            Solicitation.source_record_id == record_id,
        )
    ).scalars().all()

    assert len(records) == 1
    assert records[0].title == "Updated Roof Title"
    assert records[0].due_at.utcoffset().total_seconds() == 0

    def test_failed_batch_rolls_back(db_session):
        source_name = f"rollback_{uuid4().hex}"

        good_record = make_record(
            f"GOOD-{uuid4().hex}",
            "Valid Roof Project",
        )

        bad_record = make_record(
            "",
            "Invalid Project",
        )

        with pytest.raises(ValueError, match="source_record_id"):
            with db_session.begin_nested():
                save_or_update_solicitations(
                    db_session,
                    [good_record, bad_record],
                    source_name,
                )

        records = db_session.execute(
            select(Solicitation).where(
                Solicitation.source == source_name
            )
        ).scalars().all()

        assert records == []