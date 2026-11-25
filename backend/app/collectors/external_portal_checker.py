"""Safely checks public procurement URLs and redirects"""

import ipaddress
import socket
from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, urldefrag

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
        
def check_external_link(url):
    current_url = url

    # Does not inherit proxy config or cookies
    session = requests.Session()
    session.trust_env = False

    try:
        for _ in range(MAX_REDIRECTS + 1):
            validate_public_url(current_url)

            with session.get(
                current_url,
                allow_redirects=False,
                timeout=(5, 12),
                stream=True,
                headers={
                    "User-Agent": (
                        "ElevateSolicitationFinder/0.1"
                    ),
                    "Accept": "text/html",
                },
            ) as response:

                status = response.status_code

                if status in REDIRECT_CODES:
                    location = response.headers.get("Location")

                    if not location:
                        return LinkCheck(
                            current_url,
                            identify_provider(current_url),
                            "unavailable",
                            status,
                            "Redirect missing Location header"
                        )

                    current_url = urljoin(
                        current_url,
                        location,
                    )
                    continue

                if status in (401, 403):
                    access = "restricted"

                elif status == 404:
                    access = "unavailable"

                elif 200 <= status < 300:
                    access = "reachable"

                else:
                    access = "http_error"

                return LinkCheck(
                    destination_url=current_url,
                    provider=identify_provider(current_url),
                    access_status=access,
                    http_status=status,
                )

            return LinkCheck(
                current_url,
                identify_provider(current_url),
                "redirect_limit",
                None,
                "Too many redirects",
            )

    except (
        requests.RequestException,
        OSError,
        ValueError
    ) as exc:
        return LinkCheck(
            destination_url=None,
            provider=identify_provider(url),
            access_status="check_failed",
            http_status=None,
            error_message=str(exc) [:500],
        )

    finally:
        session.close()