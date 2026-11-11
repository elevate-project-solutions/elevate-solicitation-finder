import csv
import json
from pathlib import Path

DIRECTORY = Path(__file__).resolve().parent

CSV_PATH = DIRECTORY / "verified_export.csv"
JSON_PATH = DIRECTORY / "verified_listings.json"

def main() -> None:
    if JSON_PATH.exists():
        raise FileExistsError(
            f"{JSON_PATH} already exists. "
            "Refusing to overwrite verification work."
        )

    with CSV_PATH.open(
        encoding="utf-8-sig",
        newline="",
    ) as file:
        rows = list(csv.DictReader(file))

    records = []

    for row in rows:
        records.append(
            {
                "source_record_id": row[
                    "Solicitation ID"
                ].strip(),
                "verified": False,
                "official_url": "",
                "title": None,
                "solicitation_number": None,
                "agency_member_number": None,
                "due_date": None,
                "due_time": None,
                "status": None,
                "notes": "",
            }
        )

    JSON_PATH.write_text(
        json.dumps(records, indent=2),
        encoding="utf-8",
    )

    print(f"Prepared {len(records)} records")
    print(f"Edit: {JSON_PATH}")

if __name__ == "__main__":
    main()