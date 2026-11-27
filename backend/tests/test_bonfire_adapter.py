import pytest

from app.collectors.portal_adapters.bonfire import (
    detect_access_restriction,
)

@pytest.mark.parametrize(
    "url,title,body,status,expected",
    [
        (
            "https://txdot.bonfirehub.com/portal/",
            "Open Opportunities",
            "Log in Register Procurment Portal",
            200,
            None,
        ),
        (
            "https://account.bonfirehub.com/login?flow=123",
            "Euna Procurement Login Page",
            "Email Address Continue",
            200,
            "login_required"
        ),
        (
            "https://txdot.bonfirehub.com/opportunities/263845",
            "Just a moment...",
            "Performing security verification",
            403,
            "bot_protection",
        ),
        (
            "https://txdot.bonfirehub.com/opportunities/123",
            "Forbidden",
            "Access denied",
            403,
            "restricted",
        ),
        (
            "https://txdot.bonfirehub.com/opportunities/123",
            "Project Documents",
            "Registration is required",
            200,
            "registration_required",
        ),
        (
            "https://txdot.bonfirehub.com/opportunities/123",
            "Project Documents",
            "Project description and important dates",
            200,
            None,
        ),
    ],
)
def test_detect_access_restriction(
    url,
    title,
    body,
    status,
    expected,
):
    result = detect_access_restriction(
        url,
        title,
        body,
        status
    )

    if expected is None:
        assert result is None
    else:
        assert result is not None
        assert result[0] == expected