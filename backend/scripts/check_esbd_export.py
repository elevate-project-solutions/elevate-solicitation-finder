"""Checks a configured ESBD export without using PostgreSQL"""

import json
from pathlib import Path

from app.collectors.esbd import ESBDCollector

PAYLOAD_PATH = (
    Path(__file__).resolve().parents[1]
    / ".local"
    / "esbd"
    / "posted_payload.json"
)

ALLOWED_STATUSES = {"posted", "addendum posted"}

def main() -> None:
    payload = json.loads(PAYLOAD_PATH.read_text())

    if not isinstance(payload, dict):
        raise ValueError("ESBD payload must be a JSON object.")

    collector = ESBDCollector(export_payload=payload)
    records = collector.collect()

    if not records:
        raise ValueError(
            "ESBD returned no records. Verify the export."
        )

    statuses = {
        (record.status or "").strip().casefold()
        for record in records
    }

    unexpected = statuses - ALLOWED_STATUSES

    print(f"Collected: {len(records)}")
    print(f"Statuses: {sorted(statuses)}")
    print(f"Unexpected statuses: {sorted(unexpected)}")

    if unexpected:
        raise ValueError(
            "Export contains statuses outside the "
            "expected Posted filter"
        )

    print("Sample URLs:")

    for record in records[:5]:
        print(record.source_url)

    print("Export validation passed.")

if __name__ == "__main__":
    main()