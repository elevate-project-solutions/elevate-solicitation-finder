import csv
import json
from datetime import datetime
from pathlib import Path

DIRECTORY = Path(__file__).resolve().parent

CSV_PATH = DIRECTORY / "verified_export.csv"
JSON_PATH = DIRECTORY / "verified_listings.json"
REPORT_PATH = DIRECTORY / "validation_report.csv"

def normalize(value):
    if value is None:
        return ""

    return " ".join(str(value).split()).casefold()

def normalize_date(value):
    if not value:
        return ""

    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(
                str(value).strip(), fmt
            ).strftime("%Y-%m-%d")
        except ValueError:
            continue

    return str(value).strip()

def normalize_time(value):
    if not value:
        return ""

    for fmt in ("%I:%M %p", "%H:%M", "H%:%M:%S"):
        try:
            return datetime.strptime(
                str(value).strip(), fmt
            ).strftime("%H:%M")
        except ValueError:
            continue

    return str(value).strip()

def main():
    with CSV_PATH.open(
        encoding="utf-8-sig",
        newline="",
    ) as file:
        source = {
            row["Solicitation ID"].strip(): row
            for row in csv.DictReader(file)
        }

    verified = json.loads(
        JSON_PATH.read_text(encoding="utf-8")
    )

    comparisons = {
        "title": ("Name", normalize),
        "solicitation_number": (
            "Solicitation ID", normalize
        ),
        "agency_member_number": (
            "Agency/Texas SmartBuy Member Number",
            normalize,
        ),
        "due_date": ("Due Date", normalize_date),
        "due_time": ("Due Time", normalize_time),
        "status": ("Status", normalize),
    }

    results = []

    for expected in verified:
        record_id = expected["source_record_id"]
        actual = source.get(record_id)

        for field, (column, normalizer) in comparisons.items():
            verified_value = expected.get(field)
            source_value = (
                actual.get(column) if actual else None
            )

            if not expected.get("verified"):
                result = "NOT VERIFIED"
            elif actual is None:
                result = "MISSING"
            elif verified_value is None:
                result = "NOT VERIFIED"
            elif normalizer(source_value) == normalizer(
                verified_value
            ):
                result = "PASS"
            else:
                result = "MISMATCH"

            results.append(
                {
                    "source_record_id": record_id,
                    "field": field,
                    "csv_value": source_value,
                    "verified_value": verified_value,
                    "result": result,
                    "official_url": expected.get(
                        "official_url", ""
                    ),
                }
            )

    with REPORT_PATH.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "source_record_id",
                "field",
                "csv_value",
                "verified_value",
                "result",
                "official_url",
            ],
        )

        writer.writeheader()
        writer.writerows(results)

    for status in (
        "PASS",
        "MISMATCH",
        "MISSING",
        "NOT VERIFIED",
    ):
        count = sum(
            item["result"] == status
            for item in results
        )
        print(f"{status}: {count}")

    print(f"Report: {REPORT_PATH}")

if __name__ == "__main__":
    main()