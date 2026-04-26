"""HTTP helper with retry-on-5xx for fetcher scripts.

Wraps :mod:`urllib.request` with exponential backoff on transient server
errors. Non-retryable errors (4xx, malformed JSON, network unreachable)
surface immediately so the caller can fail loudly per the design spec.
"""

import json
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

_RETRY_DELAYS_SECONDS: tuple[float, ...] = (1.0, 2.0, 4.0)


def get_json(
    url: str,
    headers: dict[str, str],
    timeout: int = 30,
) -> dict[str, Any]:
    """Issue an HTTP GET, retry on 5xx, return the parsed JSON body.

    The function attempts the request up to four times: an initial attempt
    plus three retries with delays of 1s, 2s, and 4s. Retries are only
    triggered by 5xx HTTP status codes or by ``URLError`` raised by the
    underlying transport. Any other failure (4xx response, malformed JSON,
    DNS failure during the final attempt) raises immediately.

    Args:
        url: The full URL to GET.
        headers: A mapping of HTTP request headers. Must include any
            authentication header the endpoint requires.
        timeout: The per-attempt socket timeout in seconds.

    Returns:
        The parsed JSON body as a dict.

    Raises:
        ConnectionError: If all retry attempts return a 5xx status or
            raise ``URLError``.
        HTTPError: If the server returns a non-retryable error status (4xx).
        ValueError: If the response body is not valid JSON.
    """
    request = Request(url, headers=headers, method="GET")
    last_error: Exception | None = None

    for attempt_index in range(len(_RETRY_DELAYS_SECONDS) + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                if response.status >= 500:
                    last_error = ConnectionError(
                        f"server returned {response.status} for {url}"
                    )
                else:
                    body = response.read().decode("utf-8")
                    return json.loads(body)
        except HTTPError as exc:
            if 500 <= exc.code < 600:
                last_error = ConnectionError(f"server returned {exc.code} for {url}")
            else:
                raise
        except URLError as exc:
            last_error = ConnectionError(f"network error for {url}: {exc.reason}")

        if attempt_index < len(_RETRY_DELAYS_SECONDS):
            time.sleep(_RETRY_DELAYS_SECONDS[attempt_index])

    assert last_error is not None
    raise last_error
