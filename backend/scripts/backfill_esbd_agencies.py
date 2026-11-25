"""Backfills missing agency names on ESBD solicitations."""

import argparse
from collections import Counter

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.collectors.esbd_agencies import (
    resolve_agency_name,
)
from app.db.dependencies import get_db
from app.models.solicitation import Solicitation


def backfill_agencies(
    session: Session,
    apply_changes: bool = False,
) -> None:
    statement = select(Solicitation).where(
        Solicitation.source == "texas_esbd",
        or_(
            Solicitation.agency.is_(None),
            func.trim(Solicitation.agency) == "",
        ),
    )

    records = session.scalars(statement).all()

    resolved = 0
    unresolved = Counter()

    for record in records:
        source_record_id = record.source_record_id

        if not source_record_id or ":" not in source_record_id:
            unresolved["missing_identifier"] += 1
            continue

        agency_number = source_record_id.split(
            ":", 1
        )[0].strip().upper()

        agency_name = resolve_agency_name(
            agency_number
        )

        if agency_name is None:
            unresolved[agency_number] += 1
            continue

        if apply_changes:
            record.agency = agency_name

        resolved += 1

    if apply_changes:
        session.commit()
        print("Agency changes committed.")
    else:
        print("DRY RUN: No database changes made.")

    print(f"Records examined: {len(records)}")
    print(f"Records resolved: {resolved}")
    print(
        f"Records unresolved: {sum(unresolved.values())}"
    )

    if unresolved:
        print("\nUnresolved agency numbers:")

        for number, count in unresolved.most_common():
            print(f"{number}: {count} solicitations")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Save agency changes to the database",
    )

    args = parser.parse_args()

    dependency = get_db()
    session = next(dependency)

    try:
        backfill_agencies(
            session,
            apply_changes=args.apply,
        )
    except Exception:
        session.rollback()
        raise
    finally:
        dependency.close()