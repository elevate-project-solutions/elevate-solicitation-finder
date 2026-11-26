"""Safely checks public procurement URLs and redirects"""

import ipaddress
import socket
from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import urldefrag, urljoin, urlparse

import requests

from app.collectors.esbd_external_links import (
    identify_provider,
)

REDIRECT_CODES = {301, 302, 303, 307, 308}
MAX_REDIRECTS = 5
MAX_INSPECTION_BYTES = 256 * 1024

@dataclass(frozen=True)
class LinkCheck:
    destination_url: str | None
    provider: str
    access_status: str
    http_status: int | None
    error_message: str | None = None
    redirect_history: list[dict] = field(
        default_factory=list
    )
    content_type: str | None = None
    access_evidence: str | None = None

class AccessPageParser(HTMLParser):
    """Extracts visible text and auth indicators"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text_parts = []
        self.has_password_input = False
        self.ignored_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "template"}:
            self.ignored_depth += 1
            return

        if self.ignored_depth:
            return

        attributes = dict(attrs)

        if tag == "input":
            input_type = (
                attributes.get("type") or ""
            ).lower()

            if input_type == "password":
                self.has_password_input = True

    def handle_endtag(self, tag):
        if tag in {"script", "style", "template"}:
            self.ignored_depth = max(
                0,
                self.ignored_depth - 1,
            )

    def handle_data(self, data):
        if not self.ignored_depth:
            self.text_parts.append(data)

    @property
    def visible_text(self):
        return " ".join(
            " ".join(self.text_parts).lower().split()
        )

LOGIN_INDICATORS = (
    "login required",
    "sign in required",
    "authentication required",
    "you must log in",
    "you must sign in",
    "please log in to access",
    "please sign in to access",
    "log in to download",
    "sign in to download",
    "login to download",
)

REGISTRATION_INDICATORS = (
    "registration required",
    "registration is required",
    "you must register",
    "must be registered to",
    "register to download",
    "register to access documents",
    "registration is required to view",
    "register to view documents",
    "vendor registration is required",
    "vendor registration required",
)

BOT_PROTECTION_INDICATORS = (
    "verify you are human",
    "checking your browser",
    "checking if the site connection is secure",
    "complete the security check",
    "just a moment",
    "enable javascript and cookies to continue",
)

def validate_public_url(url):
    parsed = urlparse(url)

    if parsed.scheme != "https":
        raise ValueError("Only HTTPS URLs are allowed")

    if not parsed.hostname:
        raise ValueError("Missing hostname")

    if parsed.username or parsed.password:
        raise ValueError("Embedded credentials are not allowed")

    if parsed.port not in (None, 443):
        raise ValueError("Nonstandard ports are not allowed")

    hostname = parsed.hostname.lower()

    if hostname == "localhost":
        raise ValueError("Localhost is not allowed")

    addresses = socket.getaddrinfo(
        hostname,
        443,
        type=socket.SOCK_STREAM,
    )

    if not addresses:
        raise ValueError("No DNS addresses found")

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])

        if not ip.is_global:
            raise ValueError(
                "Non public network destination blocked"
            )
        
def classify_access(
        status_code: int,
        content_type: str,
        body: bytes,
) -> tuple[str, str]:
    """Classifies access using HTTP and page evidence"""

    if status_code == 401:
        return(
            "login_required",
            "HTTP 401 Unauthorized",
        )

    if status_code in {404, 410}:
        return (
            "unavailable",
            f"HTTP {status_code}",
        )

    media_type = content_type.split(";")[0].strip().lower()

    is_html = (
        media_type in {
            "text/html",
            "application/xhtml+xml",
        }
        or body.lstrip().lower().startswith(
            (b"<!doctype html", b"<html")
        )
    )

    if is_html:
        parser = AccessPageParser()

        parser.feed(
            body.decode(
                "utf-8",
                errors="replace",
            )
        )

        page_text = parser.visible_text

        for indicator in BOT_PROTECTION_INDICATORS:
            if indicator in page_text:
                return(
                    "bot_protection",
                    f"Page indicator: {indicator}",
                )

        if status_code == 403:
            return (
                "restricted",
                "HTTP 403 Forbidden",
            )

        if 200 <= status_code < 300:
            for indicator in REGISTRATION_INDICATORS:
                if indicator in page_text:
                    return (
                        "registration_required",
                        f"Page indicator: {indicator}",
                    )

            for indicator in LOGIN_INDICATORS:
                if indicator in page_text:
                    return (
                        "login_required",
                        f"Page indicator: {indicator}",
                    )

            if parser.has_password_input:
                return (
                    "unknown",
                    "Password input detected; "
                    "mandatory authentication not comfirmed",
                )

            return (
                "reachable",
                "HTML page reachable; "
                "document access not verified",
            )

    if status_code == 403:
        return (
            "restricted",
            "HTTP 403 Forbidden",
        )

    if not 200 <= status_code < 300:
        return (
            "http_error",
            f"HTTP {status_code}",
        )

    if body.startswith(b"%PDF-"):
        return (
            "reachable",
            "PDF file signature detected",
        )

    if body.startswith(b"PK\x03\x04"):
        return (
            "reachable",
            "ZIP-based file signature detected",
        )

    if not body:
        return (
            "unknown",
            "Successful response without content",
        )

    return (
        "unknown",
        "Successful response; content not identified",
    )

def read_response_sample(response) -> bytes:
    """Reads only enough content for access inspection"""

    sample = bytearray()

    for chunk in response.iter_content(
        chunk_size=8192
    ):
        remaining = MAX_INSPECTION_BYTES - len(sample)

        sample.extend(chunk[:remaining])

        if len(sample) >= MAX_INSPECTION_BYTES:
            break

    return bytes(sample)

def check_external_link(url):
    """Inspects external procurement access requirements"""

    current_url = urldefrag(url)[0]
    redirect_history = []
    visited_urls = set()
    last_status = None
    content_type = None

    def result(
            access_status,
            evidence=None,
            error=None,
    ):
        return LinkCheck(
            destination_url=current_url,
            provider=identify_provider(current_url),
            access_status=access_status,
            http_status=last_status,
            error_message=error,
            redirect_history=list(redirect_history),
            content_type=content_type,
            access_evidence=evidence
        )

    # Does not inherit proxy config or cookies
    session = requests.Session()
    session.trust_env = False

    try:
        for _ in range(MAX_REDIRECTS + 1):
            last_status = None
            content_type = None

            if current_url in visited_urls:
                return result(
                    "redirect_loop",
                    evidence="Repeated redirect destination",
                    error="Circular redirect detected",
                )
            
            validate_public_url(current_url)

            visited_urls.add(current_url)

            with session.get(
                current_url,
                allow_redirects=False,
                timeout=(5, 12),
                stream=True,
                headers={
                    "User-Agent": (
                        "ElevateSolicitationFinder/0.1"
                    ),
                    "Accept": (
                        "text/html,application/pdf,"
                        "application/octet-stream,*/*"
                    ),
                },
            ) as response:
                last_status = response.status_code

                content_type = response.headers.get(
                    "Content-Type"
                )

                if last_status in REDIRECT_CODES:
                    location = response.headers.get(
                        "Location"
                    )

                    if not location:
                        return result(
                            "unavailable",
                            error=(
                                "Redirect missing "
                                "Location header"
                            ),
                        )

                    next_url = urldefrag(
                        urljoin(current_url, location)
                    )[0]

                    redirect_history.append(
                        {
                            "from_url": current_url,
                            "to_url": next_url,
                            "http_status": last_status,
                        }
                    )

                    if next_url in visited_urls:
                        return result(
                            "redirect_loop",
                            evidence=(
                                "Repeated redirect destination"
                            ),
                            error="Circular redirect detected",
                        )

                    if len(redirect_history) > MAX_REDIRECTS:
                        return result(
                            "redirect_limit",
                            error="Too many redirects",
                        )

                    current_url = next_url
                    continue

                body = read_response_sample(response)

                access, evidence = classify_access(
                    last_status,
                    content_type or "",
                    body,
                )

                return result(
                    access,
                    evidence=evidence,
                )

        return result(
            "redirect_limit",
            error="Too many redirects",            
        )

    except (
        requests.RequestException,
        OSError,
        ValueError
    ) as exc:
        return result(
            "check_failed",
            error=str(exc)[:500],
        )

    finally:
        session.close()