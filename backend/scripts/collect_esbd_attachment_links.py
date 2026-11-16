import os
import time

import psycopg

from app.collectors.esbd_attachments import collect_esbd_attachments
from app.collectors.esbd_attachment_storage import (
    save_esbd_attachments,
)

def main():
    database_url = os.environ["DATABASE_URL"]

    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, solicitation_number
                FROM solicitation
                WHERE source = 'esbd'
                    AND solicitation_number IS NOT NULL
                    AND status = 'open'
                ORDER BY last_seen_at DESC
                """
            )
            solicitations = cursor.fetchall()

    print(f"Solicitations to check: {len(solicitations)}")

    total_created = 0
    total_updated = 0
    total_failed = 0

    for solicitation_id, solicitation_number in solicitations:
        try:
            attachments = collect_esbd_attachments(
                solicitation_number
            )

            with psycopg.connect(database_url) as connection:
                result = save_esbd_attachments(
                    connection, 
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

        time.sleep()

    print()
    print("Collection complete")
    print(f"New documents: {total_created}")
    print(f"Updated documents: {total_updated}")
    print(f"Failed solicitations: {total_failed}")
    print("Wow. Ev really is a computer genius.")

if __name__ == "__main__":
    main()