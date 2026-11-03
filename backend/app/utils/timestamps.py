from datetime import datetime, timezone
from zoneinfo import ZoneInfo

TEXAS_TIMEZONE = ZoneInfo("America/Chicago")

def normalize_esbd_timestamp(value: datetime | None) -> datetime | None:
    """Interprets an ESBD timestamp as Texas Central time and convert to UTC."""
    if value is None:
        return None

    if value.tzinfo is not None:
        return value.astimezone(timezone.utc)

    local_value = value.replace(tzinfo=TEXAS_TIMEZONE)

    # Rejects ambiguous local times during the spring DST transition
    round_trip = local_value.astimezone(timezone.utc).astimezone(
        TEXAS_TIMEZONE
    )
    if round_trip.replace(tzinfo=None) != value:
        raise ValueError(f"Nonexistent Texas local time: {value}")

    # Rejects ambiguous local times during the fall DST treansition
    alternate = value.replace(tzinfo=TEXAS_TIMEZONE, fold=1)
    if alternate.utcoffset() != local_value.utcoffset():
        raise ValueError(f"Ambiguous Texas local time: {value}")

    return local_value.astimezone(timezone.utc)