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
from app.collectors.esbd_document_links import (
    collect_docx_external_links,
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
        timeout=140,
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
                            AND c.last_success_at < NOW() - INTERVAL '7 days'
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

            attachments = collect_esbd_attachments(solicitation_number)

            for attachment in attachments:
                links.extend(collect_docx_external_links(attachment))

            links = list({link.url: link for link in links}.values())

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

                connection.execute(
                    text("""
                        INSERT INTO solicitation_external_link_checks (
                            solicitation_id,
                            last_checked_at,
                            last_success_at,
                            last_status,
                            failure_count,
                            next_retry_at,
                            last_error
                        )
                        VALUES (
                            :solicitation_id,
                            NOW(),
                            NOW(),
                            'success',
                            0,
                            NULL,
                            NULL
                        )
                        ON CONFLICT (solicitation_id)
                        DO UPDATE SET
                            last_checked_at = NOW(),
                            last_success_at = NOW(),
                            last_status = 'success',
                            failure_count = 0,
                            next_retry_at = NULL,
                            last_error = NULL
                    """),
                    {"solicitation_id": solicitation_id},
                )
            
            total_links += saved

        except Exception as exc:
            failures += 1
            logger.exception(
                "External link collection failed for %s",
                solicitation_number,
            )

            with engine.begin() as connection:
                connection.execute(
                    text("""
                        INSERT INTO solicitation_external_link_checks(
                            solicitation_id,
                            last_checked_at,
                            last_status,
                            failure_count,
                            next_retry_at,
                            last_error
                        )
                        VALUES (
                            :solicitation_id,
                            NOW(),
                            'failed',
                            1,
                            NOW() + INTERVAL '1 hour',
                            :error
                        )
                        ON CONFLICT (solicitation_id)
                        DO UPDATE SET
                            last_checked_at = NOW(),
                            last_status = 'failed',
                            failure_count =
                                solicitation_external_link_checks.failure_count + 1,
                            next_retry_at =
                                NOW() + (
                                    LEAST(
                                        POWER(
                                            2,
                                            solicitation_external_link_checks.failure_count
                                        ),
                                        24
                                    ) * INTERVAL '1 hour'
                                ),
                            last_error = EXCLUDED.last_error
                    """),
                    {
                        "solicitation_id": solicitation_id,
                        "error": str(exc)[:1000],
                    },
                )
        time.sleep(1)

    if failures:
        logger.warning(
            "%s solicitations failed and were scheduled for retry",
            failures,
        )

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