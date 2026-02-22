from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from xrayctl.api.client import XrayClient
from xrayctl.errors import XrayHTTPError


def _mock_response(status_code: int, json_data: Any = None, text: str = "") -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    if json_data is not None:
        resp.json.return_value = json_data
    else:
        resp.json.side_effect = ValueError("no json")
        resp.text = text
    return resp


@pytest.fixture
def client() -> XrayClient:
    return XrayClient(base_url="https://xray.example.com", token="test-token")


# --- headers ---

def test_headers_contain_bearer_token(client: XrayClient) -> None:
    headers = client._headers()
    assert headers["Authorization"] == "Bearer test-token"
    assert headers["Accept"] == "application/json"
    assert headers["Content-Type"] == "application/json"


# --- successful responses ---

def test_request_success_returns_json(client: XrayClient) -> None:
    mock_resp = _mock_response(200, json_data={"status": "ok"})
    with patch("requests.request", return_value=mock_resp) as mock_req:
        result = client.request("GET", "/xray/api/v1/system/ping")
    assert result == {"status": "ok"}
    mock_req.assert_called_once_with(
        method="GET",
        url="https://xray.example.com/xray/api/v1/system/ping",
        headers=client._headers(),
        json=None,
        params=None,
        timeout=30,
    )


def test_request_non_json_response_returns_text(client: XrayClient) -> None:
    mock_resp = _mock_response(200, text="plain text response")
    with patch("requests.request", return_value=mock_resp):
        result = client.request("GET", "/some/path")
    assert result == "plain text response"


def test_request_passes_json_body(client: XrayClient) -> None:
    mock_resp = _mock_response(200, json_data={"id": "123"})
    with patch("requests.request", return_value=mock_resp) as mock_req:
        client.request("POST", "/some/path", json_body={"key": "val"})
    assert mock_req.call_args[1]["json"] == {"key": "val"}


def test_request_passes_params(client: XrayClient) -> None:
    mock_resp = _mock_response(200, json_data=[])
    with patch("requests.request", return_value=mock_resp) as mock_req:
        client.request("GET", "/some/path", params={"page": 1})
    assert mock_req.call_args[1]["params"] == {"page": 1}


def test_base_url_trailing_slash_stripped() -> None:
    c = XrayClient(base_url="https://xray.example.com/", token="tok")
    mock_resp = _mock_response(200, json_data={})
    with patch("requests.request", return_value=mock_resp) as mock_req:
        c.request("GET", "/xray/api/v1/ping")
    assert mock_req.call_args[1]["url"] == "https://xray.example.com/xray/api/v1/ping"


# --- error responses ---

def test_request_404_raises_xray_http_error(client: XrayClient) -> None:
    mock_resp = _mock_response(404, json_data={"error": "not found"})
    with patch("requests.request", return_value=mock_resp):
        with pytest.raises(XrayHTTPError) as exc_info:
            client.request("GET", "/missing")
    assert exc_info.value.status_code == 404
    assert str(exc_info.value) == "not found"


def test_request_extracts_message_key(client: XrayClient) -> None:
    mock_resp = _mock_response(400, json_data={"message": "bad request detail"})
    with patch("requests.request", return_value=mock_resp):
        with pytest.raises(XrayHTTPError) as exc_info:
            client.request("POST", "/some/path")
    assert str(exc_info.value) == "bad request detail"


def test_request_fallback_to_http_status_when_no_message(client: XrayClient) -> None:
    mock_resp = _mock_response(500, json_data={"something": "unrecognised"})
    with patch("requests.request", return_value=mock_resp):
        with pytest.raises(XrayHTTPError) as exc_info:
            client.request("GET", "/fail")
    assert "HTTP 500" in str(exc_info.value)


def test_request_error_stores_details(client: XrayClient) -> None:
    detail = {"error": "denied", "code": 42}
    mock_resp = _mock_response(403, json_data=detail)
    with patch("requests.request", return_value=mock_resp):
        with pytest.raises(XrayHTTPError) as exc_info:
            client.request("GET", "/restricted")
    assert exc_info.value.details == detail


def test_request_uses_client_timeout() -> None:
    c = XrayClient(base_url="https://xray.example.com", token="tok", timeout=10)
    mock_resp = _mock_response(200, json_data={})
    with patch("requests.request", return_value=mock_resp) as mock_req:
        c.request("GET", "/path")
    assert mock_req.call_args[1]["timeout"] == 10
