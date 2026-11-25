"""Imports verified agency reference CSV files."""

import argparse
import csv
from pathlib import Path

OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent
    / "app"
    / "data"
    / "esbd_agencies.csv"
)

def import_agencies(
    input_path: Path,
    number_column: str,
    name_column: str,
) -> None:
    agencies: dict[str, str] = {}

    if OUTPUT_PATH.exists():
        with OUTPUT_PATH.open(
            encoding="utf-8-sig",
            newline="",
        ) as file:
            for row in csv.DictReader(file):
                agencies[row["agency_number"]] = (
                    row["agency_name"]
                )

    original_count = len(agencies)

    with input_path.open(
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        columns = reader.fieldnames or []

        if (
            number_column not in columns
            or name_column not in columns
        ):
            raise ValueError(
                f"Available columns: {columns}"
            )

        for row in reader:
            number = (
                row.get(number_column) or ""
            ).strip().upper()

            name = (
                row.get(name_column) or ""
            ).strip()

            if not number or not name:
                continue

            if number in agencies and agencies[number] != name:
                print(
                    f"Review conflict for {number}: "
                    f"{agencies[number]} vs {name}"
                )
                continue

            agencies[number] = name

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.writer(file)

        writer.writerow(
            ["agency_number", "agency_name"]
        )

        writer.writerows(
            sorted(agencies.items())
        )

    print(f"Previous agencies: {original_count}")
    print(f"New agencies: {len(agencies) - original_count}")
    print(f"Total agencies: {len(agencies)}")
    print(f"Saved to: {OUTPUT_PATH}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("input_file")
    parser.add_argument("--number-column", required=True)
    parser.add_argument("--name-column", required=True)

    args = parser.parse_args()

    import_agencies(
        Path(args.input_file),
        args.number_column,
        args.name_column,
    )