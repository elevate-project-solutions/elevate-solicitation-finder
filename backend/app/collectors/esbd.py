import csv
import io
import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.collectors.base import BaseCollector, CollectedSolicitation
from app.collectors.esbd_extraction import (
    REQUIRED_COLUMNS,
    extract_esbd_solicitation,
)

ESBD_EXPORT_URL = (
    "https://www.txsmartbuy.gov/app/extensions/"
    "CPA/CPAMain/1.0.0/services/ESBD.Service.ss"
)

class ESBDCollector(BaseCollector):
    """Retrieves ESBD listings from CSV data or an export response."""

    def __init__(
            self,
            csv_path: str | Path | None = None,
            export_payload: dict[str, Any] | None = None,
    ) -> None:
        if csv_path is None and export_payload is None:
            raise ValueError(
                "Provide csv_path or export_payload."
            )
        if csv_path is not None and export_payload is not None:
            raise ValueError(
                "Choose either csv_path or export_payload."
            )

        self.csv_path = (
            Path(csv_path) if csv_path is not None else None
        )
        self.export_payload = export_payload

    @property
    def source_name(self) -> str:
        return "texas_esbd"

    def collect(self) -> list[CollectedSolicitation]:
        if self.csv_path is not None:
            csv_text = self.csv_path.read_text(
                encoding="utf-8-sig"
            )
        else:
            csv_text = self._retrieve_export()

        return self._parse_csv(csv_text)

    def _retrieve_export(self) -> str:
        if self.export_payload is None:
            raise ValueError("Export payload is missing.")

        payload = dict(self.export_payload)
        payload["isCSV"] = True

        request = Request(
            ESBD_EXPORT_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "ElevateSolicitationFinder/0.1",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=30) as response:
                response_data = json.load(response)
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError(
                "ESBD export request failed."
            ) from exc

        if not isinstance(response_data, dict):
            raise ValueError("Unexpected ESBD response format.")

        csv_text = response_data.get("csv")

        if not isinstance(csv_text, str):
            raise ValueError(
                "ESBD response did not contain CSV text."
            )

        return csv_text

    @staticmethod
    def _parse_csv(
        csv_text: str,
    ) -> list[CollectedSolicitation]:
        reader = csv.DictReader(io.StringIO(csv_text))

        if reader.fieldnames is None:
            raise ValueError("ESBD CSV is empty.")

        reader.fieldnames = [
            name.lstrip("\ufeff").strip()
            for name in reader.fieldnames
        ]

        missing = REQUIRED_COLUMNS - set(reader.fieldnames)
        
        if missing:
            raise ValueError(
                f"ESBD CSV missing columns: {sorted(missing)}"
            )

        solicitations = []

        for row_number, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(
                    f"Malformed ESBD CSV row{row_number}."
                )

            normalized_row = {
               key: (value or "").strip()
               for key, value in row.items()
           }

            solicitation = extract_esbd_solicitation(
                normalized_row,
                row_number,
            )

            solicitations.append(solicitation)

        return solicitations