from unittest.mock import Mock

import pytest
import requests

from app.collectors import external_portal_checker
from app.collectors.external_portal_checker import (
    LinkCheck,
    check_external_link,
    classify_access,
    validate_public_url,
)

@pytest.mark.parametrize(
    "status, content_type, body, expected",
    [
        (
            200,
            "application/pdf",
            b"%PDF-1.7",
            "reachable",
        ),
        (
            200,
            "application/zip",
            b"PK\x03\x04",
            "reachable",
        ),
        (
            200,
            "text/html",
            b"<html>Public bid listing</html>",
            "login_required",
        ),
        (
            200,
            "text/html",
            b"<html>Registration required</html>",
            "registration_required",
        ),
        (
            200,
            "text/html",
            b'<input type="password">',
            "unknown",
        ),
        (
            200,
            "text/html",
            b'<a href="/register">Register</a>',
            "reachable",
        ),
        (
            200,
            "text/html",
            b'<a href="/login">Login</a>',
            "reachable",
        ),
        (
            401,
            "text/html",
            b"Unauthorized",
            "login_required",
        ),
        (
            403,
            "text/html",
            b"Forbidden",
            "restricted",
        ),
        (
            403,
            "text/html",
            b"Verify you are human",
            "bot_protection",
        ),
        (
            503,
            "text/html",
            b"Checking your browser",
            "bot_protection",
        ),
        (
            404,
            "text/html",
            b"Not found",
            "unavailable",
        ),
        (
            410,
            "text/html",
            b"Gone",
            "unavailable",
        ),
        (
            500,
            "text/html",
            b"Server error",
            "http_error",
        ),
        (
            200,
            "application/octet-stream",
            b"",
            "unknown",
        ),
    ],
)

def test_classify_access(
    status,
    content_type,
    body,
    expected,
):
    access, evidence = classify_access(
        status,
        content_type,
        body,
    )

    assert access == expected
    assert evidence

def test_ignores_script_text():
    body = (
        b"<html>"
        b"<script>"
        b'const message = "Registration required";'
        b"</script>"
        b"<p>Public procurement listings</p>"
        b"</html>"
    )

    access, _ = classify_access(
        200,
        "text/html",
        body,
    )

    assert access == "reachable"

def test_link_check_default_fields():
    check = LinkCheck(
        destination_url=None,
        provider="other",
        access_status="discovered",
        http_status=None,
    )

    assert check.redirect_history == []
    assert check.content_type is None
    assert check.access_evidence is None

def make_response(
        status,
        body=b"",
        headers=None,
):
    response = Mock()

    response.status_code = status
    response.headers = headers or {}
    response.iter_content.return_value = [body]

    response.__enter__ = Mock(
        return_value=response
    )

    response.__exit__ = Mock(
        return_value=False
    )

    return response

@pytest.fixture
def portal_session(monkeypatch):
    session = Mock()

    monkeypatch.setattr(
        external_portal_checker.requests,
        "Session",
        lambda: session,
    )

    monkeypatch.setattr(
        external_portal_checker,
        "validate_public_url",
        Mock(),
    )

    return session

def test_follows_redirect(portal_session):
    portal_session.get.side_effect = [
        make_response(
            302,
            headers={
                "Location": "/documents/specifications.pdf"
            },
        ),
        make_response(
            200,
            body=b"%PDF-1.7",
            headers={
                "Content-Type": "application/pdf"
            },
        ),
    ]

    check = check_external_link(
        "https://example.bonfirehub.com/bid"
    )

    assert check.access_status == "reachable"

    assert check.destination_url == (
        "https://example.bonfirehub.com"
        "/documents/specifications.pdf"
    )

    assert len(check.redirect_history) == 1
    assert check.redirect_history[0]["http_status"] == 302

    assert check.content_type == "application/pdf"
    assert portal_session.get.call_count == 2
    portal_session.close.assert_called_once()