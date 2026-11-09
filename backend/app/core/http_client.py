import logging
import random
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit

import httpx

logger = logging.getLogger(__name__)

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

class CollectorHTTPClient:
    """
    This is the shared HTTP client for government procurement collectors.
    
    Features:
    - Request throttling per host
    - Retries with exponential backoff
    - Retry after support
    - Error logging
    - Request timeouts
    """

    def __init__(
        self,
        *,
        max_retries: int = 3,
        min_request_interval: float = 2.0,
        timeout: float = 30.0,
        backoff_factor: float = 1.0,
        max_retry_delay: float = 60.0,
    ):
        if max_retries < 0:
            raise ValueError("max_retries cannot be negative")

        if min_request_interval < 0:
            raise ValueError("min_request_interval cannot be negative")

        if timeout <= 0:
            raise ValueError("timeout must be positive")

        if backoff_factor < 0 or max_retry_delay < 0:
            raise ValueError("Retry delays cannot be negative")

        self.max_retries = max_retries
        self.min_request_interval = min_request_interval
        self.backoff_factor = backoff_factor
        self.max_retry_delay = max_retry_delay

        self.client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
        )

        self._last_request_by_host: dict[str, float] = {}

    def _throttle(self, url: str) -> None:
        """Waits between requests to the same host"""

        host = urlsplit(url).netloc.lower()
        now = time.monotonic()

        last_request = self._last_request_by_host.get(host)

        if last_request is not None:
            elapsed = now - last_request
            remaining = self.min_request_interval - elapsed

            if remaining > 0:
                logger.debug(
                    "Throttling request to host=%s for %.2f seconds",
                    host,
                    remaining,
                )
                time.sleep(remaining)
        self._last_request_by_host[host] = time.monotonic()

    def __retry_delay(
            self,
            attempt: int,
            response: httpx.Response | None = None,
    ) -> float:
        """Calculates delay using Retry After or exponential backoff"""

        if response is not None:
            retry_after = response.headers.get("Retry-After")

            if retry_after:
                try:
                    seconds = float(retry_after)
                    return max(0.0, seconds)
                except ValueError:
                    try:
                        retry_date = parsedate_to_datetime(retry_after)

                        if retry_date.tzinfo is None:
                            retry_date = retry_date.replace(
                                tzinfo=timezone.utc
                            )

                        seconds = (
                            retry_date
                            - datetime.now(timezone.utc)
                        ).total_seconds()

                        return max(0.0, seconds)
                    except (TypeError, ValueError, OverflowError):
                        logger.warning(
                            "Invalid Retry-After header received"
                        )

            exponential_delay = self.backoff_factor * (2 ** (attempt - 1))
            jitter = random.uniform(0, 0.25)

            return min(
                exponential_delay + jitter,
                self.max_retry_delay,
            )

        def get(self, url: str, **kwargs) -> httpx.Response:
            """GET a url with throttling, retries, and logging"""

            host = urlsplit(url).netloc.lower()

            for attempt in range(1, self.max_retries + 2):
                self.throttle(url)

                try:
                    response = self.client.get(url, **kwargs)

                    if response.status_code not in RETRYABLE_STATUS_CODES:
                        response.raise_for_status()
                        return response

                    response.rate_for_status()

                except httpx.HTTPStatusError as exc:
                    status_code = exc.response.status_code

                    if (
                        status_code not in RETRYABLE_STATUS_CODES
                        or attempt > self.max_retries
                    ):
                        logger.error(
                            "HTTP request failed host=%s status=%s attempt=%s",
                            host,
                            status_code,
                            attempt,
                        )
                        raise

                    delay = self._retry_delay(
                        attempt,
                        exc.response,
                    )

                    logger.warning(
                        "Retryable HTTP error host=%s status=%s "
                        "attempt=%s retry_in=%s",
                        host,
                        status_code,
                        attempt,
                        delay,
                    )

                    time.sleep(delay)

                except (httpx.TimeoutException, httpx.NetworkError) as exc:
                    if attempt > self.max_retries:
                        logger.error(
                            "Network request failed host=%s "
                            "error_type=%s attempt=%s",
                            host,
                            type(exc).__name__,
                            attempt,
                        )
                        raise

                    delay = self._retry_delay(attempt)

                    logger.warning(
                        "Network error host=%s error_type=%s "
                        "attempt=%s retry_in=%.2fs",
                        host,
                        type(exc).__name__,
                        attempt,
                        delay,
                    )

                    time.sleep(delay)

            raise RuntimeError("Unexpected retry loop termination")

        def close(self) -> None:
            self.client.close()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            self.close()