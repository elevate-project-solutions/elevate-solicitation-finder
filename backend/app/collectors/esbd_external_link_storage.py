import json
from datetime import datetime, timezone


def save_external_links(
        connection,
        solicitation_id,
        links,
):
    """Inserts or updates external links"""

    saved = 0

    with connection.cursor() as cursor:
        for link, check in links:
            cursor.execute(
                """
                INSERT INTO solicitation_external_links (
                    solicitation_id,
                    source_url,
                    destination_url,
                    provider,
                    access_status,
                    http_status,
                    checked_at,
                    error_message,
                    redirect_history,
                    content_type,
                    access_evidence
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, 
                    %s, %s, %s::jsonb, %s, %s
                )
                ON CONFLICT (
                    solicitation_id, 
                    source_url
                )
                DO UPDATE SET
                    destination_url = EXCLUDED.destination_url,
                    provider = EXCLUDED.provider,
                    access_status = EXCLUDED.access_status,
                    http_status = EXCLUDED.http_status,
                    checked_at = EXCLUDED.checked_at,
                    error_message = EXCLUDED.error_message,
                    redirect_history = EXCLUDED.redirect_history,
                    content_type = EXCLUDED.content_type,
                    access_evidence = EXCLUDED.access_evidence
                """,
                (
                    solicitation_id,
                    link.url,
                    check.destination_url,
                    check.provider,
                    check.access_status,
                    check.http_status,
                    datetime.now(timezone.utc),
                    check.error_message,
                    json.dumps(check.redirect_history),
                    check.content_type,
                    check.access_evidence,
                ),
            )

            saved += 1

    return saved