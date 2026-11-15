from dataclasses import dataclass
from urllib.parse import urlencode, urljoin
import json
import subprocess

ESBD_DETAILS_URL = (
    "https://www.txsmartbuy.gov/app/extensions/"
    "CPA/CPAMain/1.0.0/services/ESBD.Details.Service.ss"
)

ESBD_BASE_URL = "https://www.txsmartbuy.gov"

@dataclass(frozen=True)
class ESBDAttachment:
    file_id: str
    title: str
    filename: str
    url: str
    solicitation_number: str

def collect_esbd_attachments(
        solicitation_number: str,
) -> list[ESBDAttachment]:

    solicitation_number = solicitation_number.strip()

    if not solicitation_number:
        raise ValueError("Solicitation number cannot be empty")
    
    params = {
        "c": "852252",
        "email": "",
        "identification": solicitation_number,
        "n": "2",
        "optOutKey": "",
        "urlRoot": "esbd",
    }

    query_string = urlencode(params)
    request_url = ESBD_DETAILS_URL + "?" + query_string

    result = subprocess.run(
        [
            "curl",
            "--silent",
            "--show-error",
            "--fail",
            "--max-time",
            "30",
            request_url,
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=35,
    )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        print("Request URL:", repr(request_url))
        print("Response length:", len(result.stdout))
        print("Response preview:", repr(result.stdout[:300]))

        raise ValueError(
            f"ESBD returned invalid JSON for {solicitation_number}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError("Unexpected ESBD details response")

    raw_attachments = data.get("attachments") or []

    if not isinstance(raw_attachments, list):
        raise ValueError("Unexpected ESBD attachments format")

    attachments = []

    for item in raw_attachments:
        if not isinstance(item, dict):
            continue

        file_url = item.get("fileURL")
        file_id = item.get("fileId")

        if not file_url or not file_id:
            continue

        attachments.append(
            ESBDAttachment(
                file_id=str(file_id),
                title=(
                    item.get("fileDescription")
                    or item.get("fileName")
                    or str(file_id)
                ),
                filename=item.get("fileName", ""),
                url=urljoin(ESBD_BASE_URL, file_url),
                solicitation_number=solicitation_number.strip(),
            )
        )

    return attachments