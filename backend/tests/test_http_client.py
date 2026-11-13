from unittest.mock import Mock, patch

import httpx
import pytest

from app.core.http_client import CollectorHTTPClient


def make_response(status_code: int) -> httpx.Response:
    request = httpx.Request(
        "GET",
        "https://example.test/bids",
    )
    return httpx.Response(
        status_code,
        request=request,
    )

def test_successful_request():
    with CollectorHTTPClient(
        min_request_interval=0,
    ) as client:
        client.client.get = Mock(
            return_value=make_response(200)
        )

        response = client.get(
            "https://example.test/bids"
        )

        assert response.status_code == 200
        assert client.client.get.call_count == 1

@patch("app.core.http_client.time.sleep")
def test_retries_after_server_error(mock_sleep):
    with CollectorHTTPClient(
        max_retries=2,
        min_request_interval=0,
        backoff_factor=0,
    ) as client:
        client.client.get = Mock(
            side_effect=[
                make_response(503),
                make_response(200),
            ]
        )

        response = client.get(
            "https://example.test/bids"
        )

        assert response.status_code == 200
        assert client.client.get.call_count == 2

@patch("app.core.http_client.time.sleep")
def test_stops_after_max_retries(mock_sleep):
    with CollectorHTTPClient(
        max_retries=2,
        min_request_interval=0,
        backoff_factor=0,
    ) as client:
        client.client.get = Mock(
            return_value=make_response(503)
        )

        with pytest.raises(httpx.HTTPStatusError):
            client.get("https://example.test/bids")

        assert client.client.get.call_count == 3

def test_does_not_retry_404():
    with CollectorHTTPClient(
        max_retries=3,
        min_request_interval=0,
    ) as client:
        client.client.get = Mock(
            return_value=make_response(404)
        )

        with pytest.raises(httpx.HTTPStatusError):
            client.get("https://example.test/bids")

        assert client.client.get.call_count == 1

@patch("app.core.http_client.time.sleep")
def test_retries_timeout(mock_sleep):
    with CollectorHTTPClient(
        max_retries=2,
        min_request_interval=0,
        backoff_factor=0
    ) as client:
        client.client.get = Mock(
            side_effect=[
                httpx.ReadTimeout("Timed out"),
                make_response(200),
            ]
        )

        response = client.get(
            "https://example.test/bids"
        )

        assert response.status_code == 200
        assert client.client.get.call_count == 2

@patch("app.core.http_client.time.sleep")
def test_throttles_repeated_host(mock_sleep):
    with CollectorHTTPClient(
        min_request_interval=2,
    ) as client:
        client.client.get = Mock(
            return_value=make_response(200)
        )

        client.get("https://example.test/bids/1")
        client.get("https://example.test/bids/2")

        assert mock_sleep.called

def test_retry_after_header():
    with CollectorHTTPClient(
        min_request_interval=0,
    ) as client:
        response = make_response(429)
        response.headers["Retry-After"] = "5"

        delay = client._retry_delay(
            attempt=1,
            response=response,
        )

        assert delay == 5

def test_invlaid_configuration():
    with pytest.raises(ValueError):
        CollectorHTTPClient(max_retries=-1)

    with pytest.raises(ValueError):
        CollectorHTTPClient(min_request_interval=-1)

    with pytest.raises(ValueError):
        CollectorHTTPClient(timeout=0)