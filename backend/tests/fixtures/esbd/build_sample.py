import csv
from pathlib import Path

DIRECTORY = Path(__file__).resolve().parent

SOURCE = DIRECTORY / "source_export.csv"
OUTPUT = DIRECTORY / "verified_export.csv"

REQUIRED_COLUMNS = {
    "Name",
    "Solicitation ID",
    "Due Date",
    "Due Time",
    "Agency/Texas SmartBuy Member Number",
    "Status",
    "Posting Date",
    "Created",
    "Last Modified",
    "NIGP Codes",
}

def main() -> None:
    with SOURCE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        fieldnames = reader.fieldnames or []

        missing = REQUIRED_COLUMNS - set(fieldnames)

        if missing:
            raise ValueError(
                f"Missing ESBD columns: {sorted(missing)}"
            )

        rows = list(reader)

    selected = []
    seen_ids = set()
    seen_statuses = set()

    # Selects records representing different statuses
    for row in rows:
        record_id = row["Solicitation ID"].strip()
        status = row["Status"].strip()

        if not record_id or record_id in seen_ids:
            continue

        if status not in seen_statuses:
            selected.append(row)
            seen_ids.add(record_id)
            seen_statuses.add(status)

        if len(selected) == 10:
            break

    # Fills remaining slots with unique solicitations IDs
    for row in rows:
        if len(selected) == 10:
            break

        record_id = row["Solicitation ID"].strip()

        if not record_id or record_id in seen_ids:
            continue

        selected.append(row)
        seen_ids.add(record_id)

    if len(selected) != 10:
        raise ValueError(
            "Could not select 10 unique ESBD records"
        )

    with OUTPUT.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )
        writer.writeheader()
        writer.writerows(selected)

    print(f"Selected: {len(selected)} records")
    print(f"Statuses: {sorted(seen_statuses)}")
    print(f"Saved to: {OUTPUT}")

if __name__ == "__main__":
    main()