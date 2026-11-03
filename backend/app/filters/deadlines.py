from datetime import datetime, timedelta, timezone

from app.collectors.base import CollectedSolicitation

DEFAULT_MINIMUM_DAYS = 30

def meets_deadline_requirement(
        due_at: datetime | None,
        minimum_days: int = DEFAULT_MINIMUM_DAYS,
        now: datetime | None = None,
) -> bool:
    """Checks whether a solicitation meets the minimum deadline window."""

    if minimum_days < 0:
        raise ValueError("minimum_days cannot be negative")

    if due_at is None:
        return False

    if due_at.tzinfo is None or due_at.utcoffset() is None:
        raise ValueError("due_at must be timezone-aware")

    if now is None:
        now = datetime.now(timezone.utc)

    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")

    minimum_deadline = now + timedelta(days=minimum_days)

    return due_at >= minimum_deadline

def filter_solicitations_by_deadline(
        solicitations: list[CollectedSolicitation],
        minimum_days: int = DEFAULT_MINIMUM_DAYS,
        now: datetime | None = None,
) -> list[CollectedSolicitation]:
    """Returns solicitations meeting the minimum deadline requirement."""

    if minimum_days < 0:
        raise ValueError("minimum_days cannot be negative")

    if now is None:
        now = datetime.now(timezone.utc)

    return [
        solicitation
        for solicitation in solicitations
        if meets_deadline_requirement(
            due_at=solicitation.due_at,
            minimum_days=minimum_days,
            now=now,
        )
    ]