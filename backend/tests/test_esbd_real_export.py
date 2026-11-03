from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.collectors.esbd import ESBDCollector
from app.filters.deadlines import filter_solicitations_by_deadline

CSV_PATH = Path.home() / "Downloads" / "ESBD Solicitations Export.csv"

@pytest.mark.integration
def test_real_esbd_export():
    if not CSV_PATH.exists():
        pytest.skip("Real ESBD export not found in Downloads")

    result = ESBDCollector(csv_path=CSV_PATH).run()

    now = datetime.now(timezone.utc)
    minimum_days = 30

    eligible = filter_solicitations_by_deadline(
        result.solicitations,
        minimum_days=minimum_days,
        now=now,
    )

    minimum_deadline = now + timedelta(days=minimum_days)

    assert result.total_collected > 0

    assert all(
        record.due_at is not None
        and record.due_at >= minimum_deadline
        for record in eligible
    )

    assert len(eligible) <= len(result.solicitations)

    print("\n--- REAL ESBD EXPORT RESULTS ---")
    print(f"Total collected: {result.total_collected}")
    print(f"Eligible (30+ days): {len(eligible)}")
    print(f"Excluded: {len(result.solicitations) - len(eligible)}")

    print("\nFirst 5 eligible solicitations:")
    for record in eligible[:5]:
        print(
            record.solicitation_number,
            "|",
            record.title,
            "|",
            record.due_at,
        )