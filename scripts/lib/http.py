"""HTTP helpers with retry-on-5xx for fetcher scripts.

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


def _request_with_retry(request: Request, timeout: int) -> bytes:
    """Issue ``request`` with retry-on-5xx and return the raw response body.

    Attempts the request up to four times: an initial attempt plus three
    retries with delays of 1s, 2s, and 4s. Retries fire only on 5xx HTTP
    statuses or ``URLError`` from the transport. Any other failure (4xx
    response, DNS failure during the final attempt) raises immediately.
    """
    last_error: Exception | None = None

    for attempt_index in range(len(_RETRY_DELAYS_SECONDS) + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                if response.status >= 500:
                    last_error = ConnectionError(
                        f"server returned {response.status} for {request.full_url}"
                    )
                else:
                    body: bytes = response.read()
                    return body
        except HTTPError as exc:
            if 500 <= exc.code < 600:
                last_error = ConnectionError(
                    f"server returned {exc.code} for {request.full_url}"
                )
            else:
                raise
        except URLError as exc:
            last_error = ConnectionError(
                f"network error for {request.full_url}: {exc.reason}"
            )

        if attempt_index < len(_RETRY_DELAYS_SECONDS):
            time.sleep(_RETRY_DELAYS_SECONDS[attempt_index])

    if last_error is None:
        raise RuntimeError(
            f"_request_with_retry exited the loop without recording an error "
            f"for {request.full_url}"
        )
    raise last_error


def get_json(
    url: str,
    headers: dict[str, str],
    timeout: int = 30,
) -> dict[str, Any]:
    """Issue an HTTP GET, retry on 5xx, return the parsed JSON body.

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
    body: bytes = _request_with_retry(request, timeout)
    return json.loads(body.decode("utf-8"))


def post_json(
    url: str,
    headers: dict[str, str],
    body: dict[str, Any],
    timeout: int = 30,
) -> dict[str, Any]:
    """Issue an HTTP POST with a JSON ``body``, retry on 5xx, return the parsed JSON response.

    Args:
        url: The full URL to POST.
        headers: A mapping of HTTP request headers. Should include
            ``Content-Type: application/json`` and any auth the endpoint requires.
        body: The request payload, encoded as JSON before transmission.
        timeout: The per-attempt socket timeout in seconds.

    Returns:
        The parsed JSON response as a dict.

    Raises:
        ConnectionError: If all retry attempts return a 5xx status or
            raise ``URLError``.
        HTTPError: If the server returns a non-retryable error status (4xx).
        ValueError: If the response body is not valid JSON.
    """
    payload: bytes = json.dumps(body).encode("utf-8")
    request = Request(url, data=payload, headers=headers, method="POST")
    response_body: bytes = _request_with_retry(request, timeout)
    return json.loads(response_body.decode("utf-8"))
