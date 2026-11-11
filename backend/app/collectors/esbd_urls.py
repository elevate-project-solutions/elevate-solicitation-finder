"""Builds official Texas ESBD solicitation URLs."""

from urllib.parse import quote

ESBD_BASE_URL = "https://www.txsmartbuy.gov/esbd"

def build_esbd_url(solicitation_id: str) -> str:
    """Returns a direct URL for a TX ESBD solicitatiion."""
    solicitation_id = solicitation_id.strip()

    if not solicitation_id:
        raise ValueError("Solicitation ID cannot be empty.")

    return (
        f"{ESBD_BASE_URL}/{quote(solicitation_id, safe='')}"
    )