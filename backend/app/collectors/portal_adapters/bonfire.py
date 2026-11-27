"""Browser-based inspection of Euna Bonfire portals"""

from urllib.parse import urlparse

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