"""Discovers and checks external procurement links from ESBD"""

import json
import logging
import subprocess
import time
from dataclasses import dataclass
from urllib.parse import urlencode

from sqlalchemy import text

from app.collectors.esbd_attachments import (
    ESBD_DETAILS_URL,
    collect_esbd_attachments,
)
from app.collectors.esbd_external_link_storage import (
    save_external_links,
)
from app.collectors.esbd_external_links import (
    PROVIDERS,
    extract_external_links,
    hostname_matches,
)
from app.collectors.external_portal_checker import (
    LinkCheck,
    check_external_link,
)
from app.collectors.esbd_document_links import (
    collect_docx_external_links,
)
from app.db.session import engine

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class CollectionResult:
    solicitations: int
    links_saved: int
    failures: int

def fetch_esbd_details(solicitation_number):
    params = {
        "c": "852252",
        "email": "",
        "identification": solicitation_number,
        "n": "2",
        "optOutKey": "",
        "urlRoot": "esbd",
    }

    query_string = urlencode(params)
    request_url = ESBD_DETAILS_URL + "?" + query_string

    result = subprocess.run(
        [
            "curl",
            "--silent",
            "--show-error",
            "--fail",
            "--retry",
            "3",
            "--retry-delay",
            "2",
            "--retry-all-errors",
            "--connect-timeout",
            "10",
            "--max-time",
            "30",
            request_url,
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=35,
    )

    data = json.loads(result.stdout)

    if not isinstance(data, dict):
        raise ValueError(
            "ESBD details response is not a JSON object"
        )

    return data

def check_discovered_link(link):
    """Only auto visits recognized procurement domains"""

    from urllib.parse import urlparse

    hostname = (urlparse(link.url).hostname or "").lower()

    recognized = any(
        hostname_matches(hostname, domain)
        for domain in PROVIDERS
    )

    if not recognized:
        return LinkCheck(
            destination_url=None,
            provider=link.provider,
            access_status="discovered",
            http_status=None,
            error_message=None,
        )

    return check_external_link(link.url)

def run_collection():
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT
                    s.id,
                    s.solicitation_number
                FROM solicitations s
                LEFT JOIN solicitation_external_link_checks c
                    ON c.solicitation_id = s.id
                WHERE s.source = 'texas_esbd'
                    AND s.status = 'open'
                    AND s.solicitation_number IS NOT NULL
                    AND (
                        c.solicitation_id IS NULL
                        
                        OR (
                            c.last_status = 'success'
                            AND c.last_success at < NOW() - INTERVAL '7 days'
                        )
                        
                        OR (
                            c.last_status = 'failed'
                            AND c.next_retry_at <= NOW()
                        )
                    )
                ORDER BY
                    c.last_checked_at ASC NULLS FIRST
            """)
        ).fetchall()

    logger.info(
        "Checking %s ESBD solicitations for external links",
        len(rows),
    )

    total_links = 0
    failures = 0

    for solicitation_id, solicitation_number in rows:
        try:
            data = fetch_esbd_details(solicitation_number)

            links = extract_external_links(data)

            checked_links = [
                (link, check_discovered_link(link))
                for link in links
            ]

            with engine.begin() as connection:
                saved = save_external_links(
                    connection.connection.dbapi_connection,
                    solicitation_id,
                    checked_links,
                )

            total_links += saved

            logger.info(
                "%s: %s external links",
                solicitation_number,
                saved,
            )

        except Exception:
            failures += 1
            logger.exception(
                "External link col;ection failed for %s",
                solicitation_number,
            )

        time.sleep(1)

    attachments = collect_esbd_attachments(solicitation_number)

    for attachment in attachments:
        links.extend(collect_docx_external_links(attachment))

    links = list({link.url: link for link in links}.values())

    result = CollectionResult(
        solicitations=len(rows),
        links_saved=total_links,
        failures=failures,
    )

    logger.info(
        "External links complete: "
        "solicitations=%s links=%s failures=%s",
        result.solicitations,
        result.links_saved,
        result.failures,
    )

    if failures:
        raise RuntimeError(
            f"External link collection failed for "
            f"{failures} solicitation"
        )

    return result

def main():
    logging.basicConfig(level=logging.INFO)
    result = run_collection()

    print("External link collection complete")
    print(f"Solicitations: {result.solicitations}")
    print(f"Links saved: {result.links_saved}")
    print(f"Failures: {result.failures}")

if __name__ == "__main__":
    main()