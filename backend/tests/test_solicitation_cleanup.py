import pytest
from sqlalchemy import delete
from test_solicitation_deduplication import sample

from app.models import Solicitation, SolicitationExternalRef
from app.services.solicitation_cleanup import (
    delete_confirmed_duplicate,
)
from app.services.solicitation_deduplication import (
    import_solicitation,
)

pytest_plugins = ["test_solicitation_deduplication"]

def test_cannot_delete_same_record(db, source):
    record = import_solicitation(
        db,
        **sample(source),
    )

    with pytest.raises(ValueError, match="being kept"):
        delete_confirmed_duplicate(
            db, keep_id=record.solicitation_id,
            delete_id=record.solicitation_id,
        )

def test_cannot_delete_unrelated_records(db, source):
    first = import_solicitation(
        db,
        **sample(source, "101"),
    )

    second = import_solicitation(
        db,
        **sample(
            source,
            "102",
            agency="Another City",
        ),
    )

    with pytest.raises(ValueError, match="duplicate identifier"):
        delete_confirmed_duplicate(
            db,
            keep_id=first.solicitation_id,
            delete_id=second.solicitation_id,
        )

def test_cannot_delete_record_with_external_reference(db, source):
    first = import_solicitation(
        db,
        **sample(source, "201"),
    )

    second = import_solicitation(
        db,
        **sample(source, "202"),
    )

    with pytest.raises(ValueError, match="related records"):
        delete_confirmed_duplicate(
            db,
            keep_id=first.solicitation_id,
            delete_id=second.solicitation_id,
        )

def test_deletes_unreferenced_confirmed_duplicate(db, source):
    first = import_solicitation(
        db,
        **sample(source, "301"),
    )

    second = import_solicitation(
        db,
        **sample(source, "302"),
    )

    # Removes the redundant record's external references
    db.execute(
        delete(SolicitationExternalRef).where(
            SolicitationExternalRef.solicitation_id
            == second.solicitation_id
        )
    )

    delete_confirmed_duplicate(
        db,
        keep_id=first.solicitation_id,
        delete_id=second.solicitation_id,
    )

    assert db.get(Solicitation, first.solicitation_id) is not None
    assert db.get(Solicitation, second.solicitation_id) is None