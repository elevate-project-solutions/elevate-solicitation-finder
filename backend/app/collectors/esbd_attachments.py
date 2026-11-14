from dataclasses import dataclass
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen
import json

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
    params = {
        "c": "852252",
        "email": "",
        "identification": solicitation_number.strip(),
        "n": "2",
        "optOutKey": "",
        "urlRoot": "esbd",
    }

    request_url = f"{ESBD_BASE_URL}?{urlencode(params)}"

    request = Request(
        request_url,
        headers={
            "Accept": "application/json"
            "User-Agent": "ElevateSolicitationFinder/0.1",
        },
    )

    with urlopen(request, timeout=30) as response:
        data = json.load(response)

    if not isinstance(data, dict):
        raise ValueError("Unexpected ESBD details response")

    attachments = []

    for item in data.get("attachments, []"):
        file_url = item.get("fileURL")
        file_id = item.get("fileID")

        if not file_url or not file_id:
            continue

        attachments.append(
            ESBDAttachment(
                file_id=str(file_id),
                title=item.get("fileDescription")
                or item.get("fileName")
                or str(file_id),
                filename=item.get("fileName", ""),
                url=urljoin(ESBD_BASE_URL, file_url),
                solicitation_number=solicitation_number.strip(),
            )
        )

    return attachments