import json
from unittest.mock import MagicMock

from app.collectors.esbd_external_link_storage import (
    save_external_links,
)
from app.collectors.esbd_external_links import (
    ExternalLink,
)
from app.collectors.external_portal_checker import (
    LinkCheck,
)

def test_saves_access_inspection():
    connection = MagicMock()

    cursor = (
        connection.cursor.return_value
        .__enter__.return_value
    )

    link = ExternalLink(
        url = "https://example.ionwave.net/bid",
        provider="ionwave",
    )

    history = [
        {
            "from_url": link.url,
            "to_url": (
                "https://example.ionwave.net/login"
            ),
            "http_status": 302,
        }
    ]

    check = LinkCheck(
        destination_url=(
            "https://example.ionwave.net/login"
        ),
        provider="ionwave",
        access_status="login_required",
        http_status=200,
        redirect_history=history,
        content_type="text/html",
        access_evidence="Page indicator: login required",
    )

    saved = save_external_links(
        connection,
        123,
        [(link, check)],
    )

    assert saved == 1

    cursor.execute.assert_called_once()

    query, parameters = cursor.execute.call_args.args

    assert "redirect_history" in query
    assert "content_type" in query
    assert "access_evidence" in query

    assert parameters[0] == 123
    assert parameters[1] == link.url
    assert parameters[4] == "login_required"

    assert json.loads(parameters[8]) == history
    assert parameters[9] == "text/html"

    assert parameters[10] == (
        "Page indicator: login required"
    )

def test_saves_no_links():
    connection = MagicMock()

    saved = save_external_links(
        connection,
        123,
        [],
    )

    assert saved == 0