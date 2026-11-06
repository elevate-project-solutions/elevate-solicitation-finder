from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.collectors.base import CollectedSolicitation
from app.models.solicitation import Solicitation
from app.services.solicitation_deduplication import add_duplicate_candidate


@dataclass
class UpsertResult:
    inserted: int = 0
    updated: int = 0

def normalize_status(status: str | None) -> str:
    if not status:
        return "unknown"

    normalized = status.strip().lower()

    status_map = {
        "posted": "open",
        "open": "open",
        "closed": "closed",
        "cancelled": "cancelled",
        "canceled": "cancelled",
        "awarded": "awarded",
    }

    return status_map.get(normalized, "unknown")

def find_possible_duplicates(
        session: Session,
        solicitation: Solicitation,
) -> list[Solicitation]:
    """Finds potential duplicates without automatically merging them."""

    if not solicitation.agency or not solicitation.solicitation_number:
        return []

    statement = select(Solicitation).where(
        Solicitation.id != solicitation.id,
        func.lower(func.trim(Solicitation.agency))
        == solicitation.agency.strip().lower(),
        func.lower(func.trim(Solicitation.solicitation_number))
        == solicitation.solicitation_number.strip().lower(),
    )

    return list(session.scalars(statement))

def save_or_update_solicitations(
    session: Session,
    solicitations: list[CollectedSolicitation],
    source_name: str,
) -> UpsertResult :
    """
    Inserts new solicitations or update existing records.
    
    The caller owns the transaction and must commit or rollback.
    """

    if not source_name.strip():
        raise ValueError("source_name cannot be empty")

    result = UpsertResult()
    seen_at = datetime.now(timezone.utc)

    for collected in solicitations:
        record_id = collected.source_record_id

        if not record_id or not record_id.strip():
            raise ValueError("source_record_id cannot be empty")

        if not collected.title or not collected.title.strip():
            raise ValueError("Solicitation title cannot be empty")

        if collected.due_at is not None:
            if(
                collected.due_at.tzinfo is None
                or collected.due_at.utcoffset() is None
            ):
                raise ValueError("Solicitation deadline must be timezone-aware")

        statement = select(Solicitation).where(
            Solicitation.source == source_name,
            Solicitation.source_record_id == record_id,
        )

        existing = session.execute(statement).scalar_one_or_none()

        if existing is None:
            record = Solicitation(
                source=source_name,
                source_record_id=record_id,
                agency=collected.agency_name,
                title=collected.title,
                solicitation_number=collected.solicitation_number,
                source_url=collected.source_url,
                due_at=collected.due_at,
                status=normalize_status(collected.status),
                first_seen_at=seen_at,
                last_seen_at=seen_at,
            )

            session.add(record)
            result.inserted += 1

        else:
            existing.agency = collected.agency_name
            existing.title = collected.title
            existing.solicitation_number = collected.solicitation_number
            existing.source_url = collected.source_url
            existing.due_at = collected.due_at
            existing.status = normalize_status(collected.status)
            existing.last_seen_at = seen_at
            existing.updated_at = seen_at

            result.updated += 1

        # Makes pending inserts visible to subsequent lookups
        # and surface database errors inside transactions.
        session.flush()

    return result