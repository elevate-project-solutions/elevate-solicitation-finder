from dataclasses import dataclass
from pathlib import Path

from app.collectors.esbd import ESBDCollector
from app.db.session import SessionLocal
from app.services.solicitation_upsert import save_or_update_solicitations


@dataclass
class ImportResult:
    collected: int
    inserted: int
    updated: int

def import_esbd_csv(csv_path: Path) -> ImportResult:
    """Collects ESBD records and saves them to PostgreSQL"""

    collection = ESBDCollector(csv_path=csv_path).run()

    with SessionLocal.begin() as session:
        result = save_or_update_solicitations(
            session=session,
            solicitations=collection.solicitations,
            source_name=collection.source_name,
        )

    return ImportResult(
        collected=collection.total_collected,
        inserted=result.inserted,
        updated=result.updated,
    )