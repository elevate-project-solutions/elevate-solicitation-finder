"""Manages browser resources for procurement inspection"""

from contextlib import contextmanager

from playwright.sync_api import sync_playwright

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
                page = context.new_page()

                page.set_default_timeout(15000)
                page.set_default_navigation_timeout(30000)

                yield page

            finally:
                context.close()

        finally:
            browser.close()