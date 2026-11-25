import time

from sqlalchemy import text

from app.collectors.esbd_attachment_storage import (
    save_esbd_attachments,
)
from app.collectors.esbd_attachments import collect_esbd_attachments
from app.db.session import engine


def main():
    with engine.connect() as connection:
        result = connection.execute (
            text(
                """
                SELECT id, solicitation_number
                FROM solicitations
                WHERE LOWER(TRIM(status)) IN (
                    'posted',
                    'addendum posted'
                )
                    AND solicitation_number IS NOT NULL
                ORDER BY last_seen_at DESC
                """
            #    """
            #    SELECT id, solicitation_number
            #    FROM solicitations
            #   WHERE solicitation_number = '26-15352-001'
            #    LIMIT 1
            #    """
            )
        )
        solicitations = result.fetchall()

    print(f"Solicitations to check: {len(solicitations)}")

    total_created = 0
    total_updated = 0
    total_failed = 0

    for solicitation_id, solicitation_number in solicitations:
        try:
            attachments = collect_esbd_attachments(
                solicitation_number
            )

            with engine.begin() as connection:
                result = save_esbd_attachments(
                    connection.connection.dbapi_connection, 
                    solicitation_id,
                    attachments,
                )
                connection.commit()

            total_created += result.created
            total_updated += result.updated

            print(
                f"{solicitation_number}: "
                f"{len(attachments)} attachments, "
                f"{result.created} new"
            )

        except Exception as exc:
            total_failed += 1
            print(
                f"ERROR {solicitation_number}: {exc}"
            )

        time.sleep(1)

    print()
    print("Collection complete")
    print(f"New documents: {total_created}")
    print(f"Updated documents: {total_updated}")
    print(f"Failed solicitations: {total_failed}")
    print("Wow. Ev really is a computer genius.")

if __name__ == "__main__":
    main()