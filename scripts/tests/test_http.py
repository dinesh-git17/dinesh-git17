"""Tests for the HTTP helper module."""

import json
from typing import Any
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import pytest

from scripts.lib.http import get_json, post_json


def _mock_response(status: int, body: dict[str, Any]) -> MagicMock:
    response = MagicMock()
    response.status = status
    response.read.return_value = json.dumps(body).encode("utf-8")
    response.__enter__ = lambda self: self
    response.__exit__ = lambda self, *args: None
    return response


def test_get_json_returns_parsed_body_on_200() -> None:
    response = _mock_response(200, {"hello": "world"})
    with patch("scripts.lib.http.urlopen", return_value=response):
        result = get_json("https://example.com", headers={})
    assert result == {"hello": "world"}


def test_get_json_retries_on_5xx_then_succeeds() -> None:
    fail_503 = _mock_response(503, {})
    fail_503_again = _mock_response(503, {})
    succeed = _mock_response(200, {"ok": True})
    side_effects = [fail_503, fail_503_again, succeed]
    with patch("scripts.lib.http.urlopen", side_effect=side_effects), \
         patch("scripts.lib.http.time.sleep"):
        result = get_json("https://example.com", headers={})
    assert result == {"ok": True}


def test_get_json_raises_after_persistent_5xx() -> None:
    fail = _mock_response(503, {})
    with patch("scripts.lib.http.urlopen", return_value=fail), \
         patch("scripts.lib.http.time.sleep"):
        with pytest.raises(ConnectionError, match="server returned 503"):
            get_json("https://example.com", headers={})


def test_get_json_raises_immediately_on_4xx() -> None:
    err = HTTPError("https://example.com", 401, "Unauthorized", {}, None)
    with patch("scripts.lib.http.urlopen", side_effect=err):
        with pytest.raises(HTTPError) as exc_info:
            get_json("https://example.com", headers={})
        assert exc_info.value.code == 401


def test_post_json_returns_parsed_body_on_200() -> None:
    response = _mock_response(200, {"echo": "hi"})
    with patch("scripts.lib.http.urlopen", return_value=response):
        result = post_json("https://example.com", headers={}, body={"q": 1})
    assert result == {"echo": "hi"}


def test_post_json_sends_json_encoded_body() -> None:
    response = _mock_response(200, {"ok": True})
    captured: dict[str, Any] = {}

    def fake_urlopen(request: Any, timeout: int) -> Any:
        captured["data"] = request.data
        captured["method"] = request.get_method()
        return response

    with patch("scripts.lib.http.urlopen", side_effect=fake_urlopen):
        post_json("https://example.com", headers={}, body={"q": 1, "n": 2})
    assert captured["method"] == "POST"
    assert json.loads(captured["data"].decode("utf-8")) == {"q": 1, "n": 2}


def test_post_json_retries_on_5xx_then_succeeds() -> None:
    fail = _mock_response(503, {})
    succeed = _mock_response(200, {"ok": True})
    with patch("scripts.lib.http.urlopen", side_effect=[fail, fail, succeed]), \
         patch("scripts.lib.http.time.sleep"):
        result = post_json("https://example.com", headers={}, body={})
    assert result == {"ok": True}


def test_post_json_raises_immediately_on_4xx() -> None:
    err = HTTPError("https://example.com", 422, "Unprocessable", {}, None)
    with patch("scripts.lib.http.urlopen", side_effect=err):
        with pytest.raises(HTTPError) as exc_info:
            post_json("https://example.com", headers={}, body={})
        assert exc_info.value.code == 422
