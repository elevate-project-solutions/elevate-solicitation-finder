from app.collectors.esbd_attachments import (
    collect_esbd_attachments,
)


def main():
    solicitation_number = "26-15352-001"

    attachments = collect_esbd_attachments(
        solicitation_number
    )

    print(f"Solicitation: {solicitation_number}")
    print(f"Attachments found: {len(attachments)}")

    for attachment in attachments:
        print(f"Title: {attachment.title}")
        print(f"File ID: {attachment.file_id}")
        print(f"URL: {attachment.url}")
        print()

if __name__ == "__main__":
    main()