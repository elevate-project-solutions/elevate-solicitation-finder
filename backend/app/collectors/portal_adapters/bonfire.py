import re
from urllib.parse import urlparse

from playwright.sync_api import Error as PlaywrightError

from app.collectors.external_portal_checker import (
    validate_public_url,
)
from app.collectors.portal_adapters.base import PortalAdapter
from app.collectors.portal_adapters.browser import (
    browser_page,
    is_bonfire_url,
)
from app.collectors.portal_adapters.models import (
    PortalInspection,
    PortalOpportunity,
)

BOT_PROTECTION_INDICATORS = (
    "performing security verification",
    "verify you are human",
    "checking your browser",
    "complete the security check",
    "just a moment",
)

LOGIN_INDICATORS = (
    "log in to your euna procurement account",
    "authentication required",
    "you must log in",
    "you must sign in",
    "log in to download",
    "sign in to download",
)

REGISTRATION_INDICATORS = (
    "registration required",
    "registration is required",
    "register to download",
    "register to access documents",
)

def detect_access_restriction(
        url: str,
        title: str,
        body_text: str,
        http_status: int | None = None,
) -> tuple[str, str] | None:
    """Identifies access restrictions on rendered pages"""

    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()

    page_text = " ".join(
        f"{title} {body_text}".lower().split()
    )

    for indicator in BOT_PROTECTION_INDICATORS:
        if indicator in page_text:
            return(
                "bot_protection",
                f"Page indicator: {indicator}",
            )

    if (
        hostname == "account.bonfirehub.com"
        and parsed.path.rstrip("/") == "/login"
    ):
        return (
            "login_required",
            "Redirected to Euna authentication page",
        )

    if http_status == 401:
        return (
            "login_required",
            "HTTPS 401 Unauthorized",
        )

    if http_status == 403:
        return(
            "restricted",
            "HTTP 403 Forbidden",
        )

    for indicator in REGISTRATION_INDICATORS:
        if indicator in page_text:
            return (
                "registration_required",
                f"Page indicator: {indicator}",
            )

    for indicator in LOGIN_INDICATORS:
        if indicator in page_text:
            return(
                "login_required",
                f"Page indicator: {indicator}",
            )

    return None

def normalize_text(value: str) -> str:
    """Normalizes text for conservative matching"""

    return " ".join(value.casefold().split())

def match_opportunity(
        opportunities: list[PortalOpportunity],
        solicitation_number: str | None = None,
        solicitation_title: str | None = None,
) -> tuple[PortalOpportunity | None, str | None]:
    """Finds a unique matching procurement opportunity."""

    if solicitation_number and solicitation_number.strip():
        number = normalize_text(solicitation_number)

        matches = [
            opportunity
            for opportunity in opportunities
            if normalize_text(
                opportunity.reference_number
            ) == number
        ]

        if len(matches) == 1:
            return matches[0], "reference_number"

        if len(matches) > 1:
            return None, "ambiguous_reference_number"

        return None, "reference_number_not_found"

    if solicitation_title and solicitation_title.strip():
        title = normalize_text(solicitation_title)

        matches = [
            opportunity
            for opportunity in opportunities
            if normalize_text(opportunity.title) == title
        ]

        if len(matches) == 1:
            return matches[0], "title"

        if len(matches) > 1:
            return None, "ambiguous_title"

    return None, "not_found"

def get_project_id(url: str) -> str | None:
    """Extracts the project identifier from a Bonfire URL."""

    path = urlparse(url).path

    match = re.fullmatch(
        r"/(?:opportunities/(\d)|projects/(/d+)/details)/?",
        path,
    )

    if match:
        return match.group(1) or match.group(2)

    return None

def get_listing_url(url: str) -> str:
    """Returns the agency's public opportunity listing"""

    parsed = urlparse(url)

    return (
        f"https://{parsed.hostname}"
        "/portal/?tab=openOpportunities"
    )