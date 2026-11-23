from dataclasses import dataclass

from app.collectors.esbd_attachments import ESBDAttachment

@dataclass(frozen=True)
class SaveResult:
    created: int
    updated: int

def save_esbd_attachments(
    connection,
    solicitation_id: int,
    attachments: list[ESBDAttachment],
) -> SaveResult:
    created = 0
    updated = 0

    with connection.cursor() as cursor:
        for attachment in attachments:
            cursor.execute(
                """
                SELECT id
                FROM solicitation_documents
                WHERE solicitation_id = %s
                    AND source_file_id = %s
                """,
                (solicitation_id, attachment.file_id),
            )

            existing = cursor.fetchone()

            if existing:
                document_id = existing[0]

                cursor.execute(
                    """
                    UPDATE solicitation_documents
                    SET title = %s
                    WHERE id = %s
                    """,
                    (attachment.title, document_id)
                )

                cursor.execute(
                    """
                    UPDATE document_versions
                    SET file_name = %s,
                        source_url = %s
                    WHERE document_id = %s
                        AND version_number = 1
                    """,
                    (
                        attachment.filename,
                        attachment.url,
                        document_id,
                    ),
                )

                updated += 1
                continue

            cursor.execute(
                """
                INSERT INTO solicitation_documents (
                    solicitation_id,
                    title,
                    document_type,
                    source_file_id
                )
                VALUES (%s, %s, 'other', %s)
                RETURNING id
                """,
                (
                    solicitation_id,
                    attachment.title,
                    attachment.file_id,
                ),
            )

            document_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO document_versions (
                    document_id,
                    version_number,
                    file_name,
                    source_url
                )
                VALUES (%s, 1, %s, %s)
                """,
                (
                    document_id,
                    attachment.filename,
                    attachment.url,
                ),
            )

            created += 1

    return SaveResult(created=created, updated=updated)