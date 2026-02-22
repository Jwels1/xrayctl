from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from xrayctl.api.client import XrayClient
from xrayctl.workflows.system import ping


@pytest.fixture
def mock_client() -> MagicMock:
    c = MagicMock(spec=XrayClient)
    c.project = None
    return c


def test_ping_returns_ok_true(mock_client: MagicMock) -> None:
    with patch("xrayctl.api.system.ping", return_value={"status": "pong"}):
        result = ping(mock_client)
    assert result["ok"] is True


def test_ping_wraps_api_response(mock_client: MagicMock) -> None:
    api_response = {"status": "pong", "version": "3.8.0"}
    with patch("xrayctl.api.system.ping", return_value=api_response):
        result = ping(mock_client)
    assert result["response"] == api_response


def test_ping_calls_api_with_client(mock_client: MagicMock) -> None:
    with patch("xrayctl.api.system.ping", return_value={}) as mock_api:
        ping(mock_client)
    mock_api.assert_called_once_with(mock_client)
