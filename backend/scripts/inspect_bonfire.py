"""Inspects the rendered structure of Bonfire pages."""

import argparse
import json

from app.collectors.external_portal_checker import (
    validate_public_url,
)
from app.collectors.portal_adapters.browser import (
    browser_page,
    is_bonfire_url,
)

def inspect_page(url: str):
    if not is_bonfire_url(url):
        raise ValueError("Unsupported Bonfire URL")

    validate_public_url(url)

    with browser_page() as page:
        blocked_hosts = set()

        def record_failed_request(request):
            from urllib.parse import urlparse

            hostname = urlparse(request.url).hostname

            if hostname:
                blocked_hosts.add(hostname)

        page.on(
            "requestfailed",
            record_failed_request,
        )

        response = page.goto(
            url,
            wait_until="domcontentloaded",
        )

        page.wait_for_timeout(5000)

        result = {
            "source_url": url,
            "destination_url": page.url,
            "http_status": (
                response.status if response else None
            ),
            "title": page.title(),
            "body_text": (
                page.locator("body").inner_text()[:12000]
            ),
            "links": page.locator("a[href]").evaluate_all(
                """
                elements => elements.slice(0, 150).map(
                    element => ({
                        text: element.innerText.trim(),
                        href: element.href
                    })
                )
                """
            ),
            "buttons": page.get_by_role(
                "button"
            ).all_text_contents(),
            "password_inputs": page.locator(
                'input[type="password"]'
            ).count(),
            "failed_request_hosts": sorted(blocked_hosts),
        }

        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("url")

    args = parser.parse_args()

    inspect_page(args.url)