"""Manages browser resources for procurement inspection"""

from contextlib import contextmanager

from playwright.sync_api import sync_playwright

from urllib.parse import urlparse

from app.collectors.external_portal_checker import (
    validate_public_url,
)

BONFIRE_DOMAINS = (
    "bonfire.com",
    "gobonfire.com",
    "bonfirehub.com"
)

def is_bonfire_url(url: str) -> bool:
    """Checks whether a URL belongs to Bonfire."""

    try:
        parsed = urlparse(url)

        if parsed.scheme != "https":
            return False

        if parsed.username or parsed.password:
            return False

        if parsed.port not in (None, 443):
            return False

        hostname = (parsed.hostname or "").lower()

        return any(
            hostname == domain
            or hostname.endswith("." + domain)
            for domain in BONFIRE_DOMAINS
        )

    except ValueError:
        return False

def restrict_bonfire_requests(route):
    """Blocks requests outside supported public domains"""

    url = route.request.url

    if not is_bonfire_url(url):
        route.abort()
        return

    try:
        validate_public_url(url)

    except (ValueError, OSError):
        route.abort()
        return

    route.continue_()

@contextmanager
def browser_page():
    """Creates an isolated browser page for inspection"""

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
        )

        try:
            context = browser.new_context(
                accept_downloads=False,
                ignore_https_errors=False,
                service_workers="block",
            )

            try:
                context.route("**/*", restrict_bonfire_requests)
                page = context.new_page()

                page.set_default_timeout(15000)
                page.set_default_navigation_timeout(30000)

                yield page

            finally:
                context.close()

        finally:
            browser.close()