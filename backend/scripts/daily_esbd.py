"""Downloads, validates, imports and cleans up an ESBD CSV."""

import argparse
import fcntl
import json
import logging
import tempfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.collectors.esbd import ESBDCollector
from app.services.esbd_import import import_esbd_csv

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parents[1]

LOCAL_DIR = BACKEND_DIR / ".local" / "esbd"

PAYLOAD_PATH = LOCAL_DIR / "posted_payload.json"

DOWNLOAD_DIR = LOCAL_DIR / "downloads"

LOCK_PATH = LOCAL_DIR / "daily_esbd.lock"

ALLOWED_STATUSES = {"posted", "addendum posted"}

def load_export_payload(
        payload_path: Path = PAYLOAD_PATH,
) -> dict:
    """Reads the verified ESBD request payload"""

    payload = json.loads(
        payload_path.read_text(encoding="utf-8")
    )

    if not isinstance(payload, dict):
        raise ValueError(
            "ESBD export payload must be a JSON object."
        )

    if not payload:
        raise ValueError(
            "ESBD export payload cannot be empty."
        )

    return payload

def validate_records(records: list) -> None:
    """Rejects empty or unexpectedly filtered exports"""

    if not records:
        raise ValueError(
            "ESBD export contained zero solicitations"
        )

    unexpected_statuses = {
        (record.status or "").strip().casefold()
        for record in records
        if (record.status or "").strip().casefold()
        not in ALLOWED_STATUSES
    }

    if unexpected_statuses:
        raise ValueError(
            "Unexpected ESBD statuses: "
            f"{sorted(unexpected_statuses)}"
        )

    for record in records:
        if not record.source_record_id:
            raise ValueError("Missing source record ID.")

        if not record.source_url:
            raise ValueError(
                "Missing official solicitation URL."
            )

def save_temporary_csv(
    csv_text: str,
    download_dir: Path = DOWNLOAD_DIR,
) -> Path:
    """Saves an export to a uniquely named temporary file."""

    download_dir.mkdir(
        parents=True,
        exist_ok=True,
        mode=0o700,
    )

    timestamp = datetime.now(
        ZoneInfo("America/Chicago")
    ).strftime("%Y%m%d_%H%M%S")

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        prefix=f"esbd_{timestamp}_",
        suffix=".csv",
        dir=download_dir,
        delete=False,
    ) as file:
        file.write(csv_text)
        return Path(file.name)

@contextmanager
def exclusive_run_lock(
    lock_path: Path = LOCK_PATH,
):
    """Prevents simultaneous daily imports."""

    lock_path.parent.mkdir(
        parents=True,
        exist_ok=True,
        mode=0o700,
    )

    with lock_path.open("a+") as lock_file:
        try:
            fcntl.flock(
                lock_file.fileno(),
                fcntl.LOCK_EX | fcntl.LOCK_NB,
            )
        except BlockingIOError as exc:
            raise RuntimeError(
                "Another ESBD import is already running."
            ) from exc

        try:
            yield
        finally:
            fcntl.flock(
                lock_file.fileno(),
                fcntl.LOCK_UN,
            )

def run_daily_import(
        payload_path: Path = PAYLOAD_PATH,
        download_dir: Path = DOWNLOAD_DIR,
):
    """
    Downloads, validates, imports, and removes the CSV.
    
    A failed import retains the CSV for investigation.
    """

    payload = load_export_payload(payload_path)

    collector = ESBDCollector(
        export_payload=payload
    )

    logger.info("Requesting latest ESBD export")

    csv_text = collector._retrieve_export()

    # Validates before writing anything to the database

    records = collector._parse_csv(csv_text)

    validate_records(records)

    csv_path = save_temporary_csv(
        csv_text,
        download_dir,
    )

    logger.info(
        "Downloaded %s ESBD records to %s",
        len(records),
        csv_path,
    )

    try:
        result = import_esbd_csv(csv_path)

    except Exception:
        logger.exception(
            "ESBD import failed. CSV retained at %s",
            csv_path,
        )
        raise

    # Only removes the CSV after import_esbd_csv succeeds.
    csv_path.unlink()

    logger.info(
        "ESBD import succeeded. "
        "Collected=%s Inserted=%s Update=%s",
        result.collected,
        result.inserted,
        result.updated,
    )

    return result

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the daily ESBD import."
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Download and validate without importing",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s %(levelname)s "
            "%(name)s %(message)s"
        ),
    )

    with exclusive_run_lock():
        if args.dry_run:
            payload = load_export_payload()

            collector = ESBDCollector(
                export_payload=payload
            )

            records = collector.collect()

            validate_records(records)

            print(
                f"Dry run successful: {len(records)} records"
            )

            return

        result = run_daily_import()

        print("Daily ESBD import complete")
        print(f"Collected: {result.collected}")
        print(f"Inserted: {result.inserted}")
        print(f"Updated: {result.updated}")

if __name__ == "__main__":
    main()