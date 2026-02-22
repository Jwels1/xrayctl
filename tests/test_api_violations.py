"""Tests for xrayctl/api/violations.py — thin REST wrapper."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from xrayctl.api import violations
from xrayctl.api.client import XrayClient


@pytest.fixture
def mock_client() -> MagicMock:
    c = MagicMock(spec=XrayClient)
    c.project = None
    return c


@pytest.fixture
def mock_client_with_project() -> MagicMock:
    c = MagicMock(spec=XrayClient)
    c.project = "my-project"
    return c


def test_list_violations_calls_correct_endpoint(mock_client: MagicMock) -> None:
    violations.list_violations(mock_client)
    mock_client.request.assert_called_once()
    args, kwargs = mock_client.request.call_args
    assert args[0] == "POST"
    assert args[1] == "/xray/api/v1/violations"


def test_list_violations_body_contains_filters(mock_client: MagicMock) -> None:
    f = {"severities": ["High"], "cve": "CVE-2024-1234"}
    violations.list_violations(mock_client, filters=f)
    _, kwargs = mock_client.request.call_args
    assert kwargs["json_body"]["filters"] == f


def test_list_violations_body_contains_pagination(mock_client: MagicMock) -> None:
    violations.list_violations(
        mock_client, order_by="updated", direction="desc", limit=10, offset=20
    )
    _, kwargs = mock_client.request.call_args
    pagination = kwargs["json_body"]["pagination"]
    assert pagination["order_by"] == "updated"
    assert pagination["direction"] == "desc"
    assert pagination["limit"] == 10
    assert pagination["offset"] == 20


def test_list_violations_includes_project_key_when_set(mock_client_with_project: MagicMock) -> None:
    violations.list_violations(mock_client_with_project)
    _, kwargs = mock_client_with_project.request.call_args
    assert kwargs["params"]["projectKey"] == "my-project"


def test_list_violations_no_project_key_when_none(mock_client: MagicMock) -> None:
    violations.list_violations(mock_client)
    _, kwargs = mock_client.request.call_args
    assert kwargs["params"] is None
