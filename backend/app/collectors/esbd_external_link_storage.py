from datetime import datetime, timezone

def save_external_links(
        connection,
        solicitation_id,
        links,
):
    """Inserts or updates external links without duplicates"""

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
                    error_message
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (solicitation_id, source_url)
                DO UPDATE SET
                    destination_url = EXCLUDED.destination_url,
                    provider = EXCLUDED.provider,
                    access_status = EXCLUDED.access_status,
                    http_status = EXCLUDED.http_status,
                    checked_at = EXCLUDED.checked_at,
                    error_message = EXCLUDED.error_message
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
                ),
            )

            saved += 1

    return saved