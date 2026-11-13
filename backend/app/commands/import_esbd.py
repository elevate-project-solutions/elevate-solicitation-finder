import argparse
from pathlib import Path

from app.core.logging_config import configure_logging
from app.services.esbd_import import import_esbd_csv


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import ESBD solicitations from CSV"
    )

    parser.add_argument(
        "csv_path",
        type=Path,
        help="Path to ESBD CSV export",
    )

    args = parser.parse_args()

    configure_logging()

    result = import_esbd_csv(args.csv_path)

    print(f"Collected: {result.collected}")
    print(f"Inserted: {result.inserted}")
    print(f"Updated: {result.updated}")

if __name__ == "__main__":
    main()