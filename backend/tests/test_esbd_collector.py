import json
from datetime import datetime
from urllib.error import URLError

import pytest

from app.collectors.esbd import ESBDCollector

CSV_TEXT = (
    "Name,Solicitation ID,Due Date,Due Time,"
    "Agency/Texas SmartBuy Member Number,Status,"
    "Posting Date,Created,Last Modified,NIGP Codes\n"
    "Roof Replacement,RFP-123,11/12/2026,3:00 PM,"
    "719,Posted,10/21/2026,"
    "10/21/2026 5:26 pm,"
    "10/21/2026 5:27 pm,"
    '"91438-Roofing; 91066-Roof Repair;"\n'
)

def test_collector_reads_csv_file(tmp_path):
    path = tmp_path / "esbd.csv"
    path.write_text(CSV_TEXT, encoding="utf-8")

    result = ESBDCollector(csv_path=path).run()

    assert result.source_name == "texas_esbd"
    assert result.total_collected == 1

    record = result.solicitations[0]

    assert record.title == "Roof Replacement"
    assert record.source_record_id == "719:RFP-123"
    assert record.solicitation_number == "RFP-123"
    assert record.status == "Posted"
    assert record.agency_name is None
    assert record.source_url is None
    assert record.due_at == datetime(2026, 11, 12, 15, 0)
    assert len(record.raw_data["nigp_codes"]) == 2

def test_collector_supports_empty_csv(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text(
        CSV_TEXT.splitlines()[0] + "\n",
        encoding="utf-8",
    )

    assert ESBDCollector(csv_path=path).run().total_collected == 0

def test_collector_rejects_missing_columns(tmp_path):
    path = tmp_path / "invalid.csv"
    path.write_text("Name,Solicitation ID \nExample,123\n")

    with pytest.raises(ValueError, match="missing columns"):
        ESBDCollector(csv_path=path).run()

def test_collector_rejects_invalid_date(tmp_path):
    path = tmp_path / "invalid_date.csv"
    path.write_text(
        CSV_TEXT.replace("11/12/2026", "not-a-date")
    )

    with pytest.raises(ValueError, match="Invalid ESBD"):
        ESBDCollector(csv_path=path).run()

def test_collector_requires_one_input():
    with pytest.raises(ValueError):
        ESBDCollector()

    with pytest.raises(ValueError):
        ESBDCollector(
            csv_path="test.csv",
            export_payload={"status": "1"},
        )

def test_collector_retrieves_json_csv_response(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, *_args):
            return json.dumps(
                {"csv": CSV_TEXT}
            ).encode("utf-8")

    def fake_urlopen(request, timeout):
        assert timeout == 30
        assert request.get_method() == "POST"
        payload = json.loads(request.data)
        assert payload["isCSV"] is True
        assert payload["status"] == "1"
        return FakeResponse()

    monkeypatch.setattr(
        "app.collectors.esbd.urlopen",
        fake_urlopen,
    )

    collector = ESBDCollector(
        export_payload={"status": "1"}
    )

    assert collector.run().total_collected == 1

def test_collector_rejects_missing_csv_response(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, *args):
            return b'{"agencies": []}'

    monkeypatch.setattr(
        "app.collectors.esbd.urlopen",
        lambda *_args, **_kwargs: FakeResponse(),
    )

    with pytest.raises(ValueError, match="CSV text"):
        ESBDCollector(export_payload={}).run()

def test_collector_reports_network_failure(monkeypatch):
    def fail(*_args, **_kwargs):
        raise URLError("connection failed")

    monkeypatch.setattr(
        "app.collectors.esbd.urlopen",
        fail,
    )

    with pytest.raises(RuntimeError, match="request failed"):
        ESBDCollector(export_payload={}).run()