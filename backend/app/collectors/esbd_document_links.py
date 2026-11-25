import io
import re
import zipfile
from urllib.parse import urlparse
from xml.etree import ElementTree

import requests

from app.collectors.esbd_external_links import (
    ExternalLink,
    identify_provider,
)

MAX_DOCX_SIZE = 8 * 1024 * 1024

URL_PATTERN = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)

def extract_docx_external_links(document_bytes: bytes) -> list[ExternalLink]:
    """Extracts external procurement links from a DOCX file."""
    found: dict[str, ExternalLink] = {}

    with zipfile.ZipFile(io.BytesIO(document_bytes)) as archive:
        for filename in archive.namelist():
            if not filename.startswith("word/"):
                continue

            if not filename.endswith((".xml", ".rels")):
                continue

            root = ElementTree.fromstring(archive.read(filename))

            for element in root.iter():
                values = list(element.attrib.values())

                if element.text:
                    values.append(element.text)

                for value in values:
                    for match in URL_PATTERN.findall(value):
                        url = match.rstrip(".,;)]}")

                        parsed = urlparse(url)

                        if parsed.scheme != "https":
                            continue

                        if parsed.hostname is None:
                            continue

                        if parsed.hostname.endswith("txsmartbuy.gov"):
                            continue

                        found[url] = ExternalLink(
                            url=url,
                            provider=identify_provider(url),
                        )

    return list(found.values())

def collect_docx_external_links(attachment) -> list[ExternalLink]:
    """Downloads a DOCX attachment and extracts external links"""
    if isinstance(attachment, dict):
        url = (
            attachment.get("url")
            or attachment.get("file_url")
            or attachment.get("fileUrl")
        )
        filename = (
            attachment.get("name")
            or attachment.get("filename")
            or ""
        )
    else:
        url = getattr(attachment, "url", None)
        filename = getattr(attachment, "filename", "")

    if not url:
        return []

    parsed = urlparse(url)

    if parsed.scheme != "https":
        return []

    if parsed.hostname not in {
        "www.txsmartbuy.gov",
        "txsmartbuy.gov",
    }:
        return []

    if not (
        filename.lower().endswith(".docx")
        or parsed.path.lower().endswith(".docx")
    ):
        return []

    response = requests.get(
        url,
        timeout=30,
        stream=True,
    )
    response.raise_for_status()

    document = bytearray()

    with response:
        for chunk in response.iter_content(chunk_size=65536):
            document.extend(chunk)

            if len(document) > MAX_DOCX_SIZE:
                raise ValueError("DOCX attachment exceeds 8 MB limit")

    return extract_docx_external_links(bytes(document))