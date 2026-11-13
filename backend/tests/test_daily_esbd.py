from types import SimpleNamespace

import pytest

from scripts import daily_esbd


def make_record(
    status="Posted",
    source_url="https:///www.txsmartbuy.gov/esbd/ABC-123",
):
    return SimpleNamespace(
        status=status,
        source_record_id="M0152:ABC-123",
        source_url=source_url,
    )

def test_accepts_posted_records():
    daily_esbd.validate_records([
        make_record("Posted"),
    ])

def test_accepts_addendum_posted_records():
    daily_esbd.validate_records([
        make_record("Addendum Posted"),
    ])

def test_rejects_awarded_records():
    with pytest.raises(ValueError):
        daily_esbd.validate_records([
            make_record("Awarded"),
        ])

def test_rejects_empty_export():
    with pytest.raises(ValueError):
        daily_esbd.validate_records([])

def test_rejects_missing_url():
    with pytest.raises(ValueError):
        daily_esbd.validate_records([
            make_record(source_url=None),
        ])

def test_temporary_csv_is_created(tmp_path):
    path = daily_esbd.save_temporary_csv(
        "Name,Status\nTest,Posted\n",
        tmp_path,
    )

    assert path.exists()
    assert path.suffix == ".csv"

    assert "Test,Posted" in path.read_text()

def test_successful_import_deletes_csv(
        tmp_path,
        monkeypatch,
):
    payload_path = tmp_path / "payload.json"
    payload_path.write_text('{"test": true}')

    class FakeCollector:
        def __init__(self, export_payload):
            self.export_payload = export_payload

        def _retrieve_export(self):
            return "fake,csv\n"

        def _parse_csv(self, csv_text):
            return [make_record()]

    def fake_import(csv_path):
        assert csv_path.exists()

        return SimpleNamespace(
            collected=1,
            inserted=1,
            updated=0,
        )

    monkeypatch.setattr(
        daily_esbd,
        "ESBDCollector",
        FakeCollector,
    )

    monkeypatch.setattr(
        daily_esbd,
        "import_esbd_csv",
        fake_import,
    )

    download_dir = tmp_path / "downloads"

    result = daily_esbd.run_daily_import(
        payload_path,
        download_dir,
    )

    assert result.inserted == 1

    assert list(download_dir.glob("*.csv")) == []

def test_failed_import_retains_csv(
        tmp_path,
        monkeypatch,
):
    payload_path = tmp_path / "payload.json"
    payload_path.write_text('{"test": true}')

    class FakeCollector:
        def __init__(self, export_payload):
            self.export_payload = export_payload

        def _retrieve_export(self):
            return "fake,csv\n"

        def _parse_csv(self, csv_text):
            return [make_record()]

    def fake_import(csv_path):
        raise RuntimeError("Database unavailable")

    monkeypatch.setattr(
        daily_esbd,
        "ESBDCollector",
        FakeCollector,
    )

    monkeypatch.setattr(
        daily_esbd,
        "import_esbd_csv",
        fake_import,
    )

    download_dir = tmp_path / "downloads"

    with pytest.raises(
        RuntimeError,
        match="Database unavailable",
    ):
        daily_esbd.run_daily_import(
            payload_path,
            download_dir,
        )

    retained_files = list(
        download_dir.glob("*.csv")
    )

    assert len(retained_files) == 1
    assert retained_files[0].exists()

def test_rejects_missing_payload(tmp_path):
    with pytest.raises(FileNotFoundError):
        daily_esbd.load_export_payload(
            tmp_path / "missing.json"
        )

def test_rejects_invalid_payload(tmp_path):
    payload_path = tmp_path / "payload.json"
    payload_path.write_text("[]")

    with pytest.raises(ValueError):
        daily_esbd.load_export_payload(
            payload_path
        )