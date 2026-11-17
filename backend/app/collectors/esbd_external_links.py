"""Extracts external procurement URLs from ESBD details JSON"""

import html
import json
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import urlparse, urlunparse

from app.collectors.esbd_attachments import ESBD_BASE_URL

@dataclass(frozen=True)
class ExternalLink:
    url: str
    provider: str

PROVIDERS = {
    "bonfirehub.com": "euna_bonfire",
    "gobonfire.com": "euna_bonfire",
    "ionwave.net": "ionwave",
    "civcastusa.com": "civcast",
    "bidnetdirect.com": "bidnet",
    "planetbids.com": "planetbids",
    "opengov.com": "opengov",
    "bidsandtenders.com": "bidsandtenders",
    "publicpurchase.com": "publicpurchase",
    "demandstar.com": "demandstar",
}

EXCLUDED_DOMAINS = {
    "txsmartbuy.gov",
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "youtube.com",
    "x.com",
    "twitter.com",
}

URL_PATTERN = re.compile(
    r"https?://[^\s<>\"']+",
    re.IGNORECASE,
)

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return

        for name, value in attrs:
            if name.lower() == "href" and value:
                self.links.append(value)

def hostname_matches(hostname, domain):
    return (
        hostname == domain
        or hostname.endswith("." + domain)
    )

def identify_provider(url):
    hostname = (urlparse(url).hostname or "").lower()

    for domain, provider in PROVIDERS.items():
        if hostname_matches(hostname, domain):
            return provider

    return "other"

def normalize_url(value):
    if not isinstance(value, str):
        return None

    value = html.unescape(value).strip()
    value = value.rstrip(".,;)>]")

    parsed = urlparse(value)

    if parsed.scheme.lower() not in {"http", "https"}:
        return None

    if not parsed.hostname:
        return None

    if parsed.username or parsed.password:
        return None

    if parsed.port not in (None, 80, 443):
        return None

    hostname = parsed.hostname.lower()

    if hostname == "localhost":
        return None

    if any(
        hostname_matches(hostname, domain)
        for domain in EXCLUDED_DOMAINS
    ):
        return None

    return urlunparse(parsed._replace(fragment=""))

def extract_urls_from_text(value):
    if not isinstance(value, str):
        return []

    value = html.unescape(value)
    parser = LinkParser()

    try:
        parser.feed(value)
    except Exception:
        pass

    candidates = list(parser.links)
    candidates.extend(URL_PATTERN.findall(value))

    return candidates

def collect_text_values(value, depth=0):
    """Walks JSON values, excluding attachment metadata"""

    if depth > 12:
        return

    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in {
                "attachments",
                "fileurl",
                "fileid",
                "filename",
            }:
                continue

            yield from collect_text_values(child, depth + 1)

    elif isinstance(value, list):
        for child in value:
            yield from collect_text_values(child, depth + 1)

    elif isinstance(value, str):
        yield value

def extract_external_links(data):
    """Returns unique external links from ESBD JSON."""

    found = {}

    for text_value in collect_text_values(data):
        for candidate in extract_urls_from_text(text_value):
            url = normalize_url(candidate)

            if url is None:
                continue

            found[url] = ExternalLink(
                url=url,
                provider=identify_provider(url),
            )

    return list(found.value())