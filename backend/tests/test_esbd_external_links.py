from app.collectors.esbd_external_links import (
    extract_external_links,
    identify_provider,
    normalize_url,
)


def test_identifies_euna_bonfire():
    assert identify_provider(
        "https://erstexas.bonfirehub.com/portal"
    ) == "euna_bonfire"

def test_extracts_url_from_description():
    data = {
        "description": (
            "Download the RFP at "
            "https://erstexas.bonfirehub.com/portal"
        ),
        "attachments": [],
    }

    links = extract_external_links(data)

    assert len(links) == 1
    assert links[0].provider == "euna_bonfire"

def test_extracts_html_links():
    data = {
        "description": (
            '<a href="https://example.ionwave.net">'
            "Bid Documents</a>"
        )
    }

    links = extract_external_links(data)

    assert len(links) == 1
    assert links[0].provider == "ionwave"

def test_deduplicates_links():
    url = "https://erstexas.bonfirehub.com/portal"

    data = {
        "description": url,
        "instructions": url,
    }

    assert len(extract_external_links(data)) == 1

def test_ignores_esbd_links():
    data = {
        "description": (
            "https://www.txsmartbuy.gov/esbd/26-15352-001"
        )
    }

    assert extract_external_links(data) == []

def test_rejects_non_http_urls():
    assert normalize_url(
        "javascript:alert(1)"
    ) is None

def test_keeps_unrecognized_external_sites():
    data = {
        "description": "https://procurement.example.org/bid"
    }

    links = extract_external_links(data)

    assert len(links) == 1
    assert links[0].provider == "other"