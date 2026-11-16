import json
import subprocess
from unittest.mock import patch

import pytest

from app.collectors.esbd_attachments import (
    collect_esbd_attachments,
)

def mock_curl_response(attachments):
    return subprocess.CompletedProcess(
        args=["curl"],
        returncode=0,
        stdout=json.dumps({"attachments": attachments}),
        stderr="",
    )

def test_collects_attachment():
    response = mock_curl_response(
        [
            {
                "fileId": "34076590",
                "fileName": "example.docx",
                "fileDescription": "Example Document",
                "fileURL": "/core/media/media.nl?id=34076590",
            }
        ]
    )

    with patch("subprocess.run", return_value=response):
        attachments = collect_esbd_attachments("26-15352-001")

    assert len(attachments) == 1
    assert attachments[0].file_id == "34076590"
    assert attachments[0].filename == "example.docx"
    assert attachments[0].title == "Example Document"
    assert attachments[0].url == (
        "https://www.txsmartbuy.gov/core/media/media.nl?id=34076590"
    )

def test_handles_no_attachments():
    with patch(
        "subprocess.run",
        return_value=mock_curl_response([]),
    ):
        attachments = collect_esbd_attachments("26-15352-001")

    assert attachments == []

def test_skips_incomplete_attachments():
    response = mock_curl_response(
        [
            {"fileId": "123"},
            {"fileURL": "/core/media/media/nl?id=456"},
        ]
    )

    with patch("subprocess.run", return_value=response):
        attachments = collect_esbd_attachments("26-15352-001")

    assert attachments == []

def test_rejects_empty_solicitation_number():
    with pytest.raises(ValueError):
        collect_esbd_attachments(" ")

def test_rejects_invalid_json():
    response = subprocess.CompletedProcess(
        args=["curl"],
        returncode=0,
        stdout="<html>Not JSON</html>",
        stderr="",
    )

    with patch("subprocess.run", return_value=response):
        with pytest.raises(ValueError, match="invalid JSON"):
            collect_esbd_attachments("26-15352-001")