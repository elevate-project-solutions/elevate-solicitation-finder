import logging
from dataclasses import dataclass
from pathlib import Path

from app.collectors.esbd import ESBDCollector
from app.db.session import SessionLocal
from app.services.collector_runner import run_collector
from app.services.solicitation_upsert import save_or_update_solicitations

logger = logging.getLogger(__name__)

@dataclass
class ImportResult:
    collected: int
    inserted: int
    updated: int

def import_esbd_csv(csv_path: Path) -> ImportResult:
    """Collects ESBD records and saves them to PostgreSQL"""

    collection = run_collector(
        ESBDCollector(csv_path=csv_path)
    )

    try:
        with SessionLocal.begin() as session:
            result = save_or_update_solicitations(
                session=session,
                solicitations=collection.solicitations,
                source_name=collection.source_name,
            )

    except Exception:
        logger.exception(
            "ESBD database import failed"
        )
        raise

    logger.info(
        "ESBD import completed collected=%s inserted=%s updated=%s",
        collection.total_collected,
        result.inserted,
        result.updated,
    )

    return ImportResult(
        collected=collection.total_collected,
        inserted=result.inserted,
        updated=result.updated,
    )