"""Tests for xrayctl/workflows/violations.py."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from xrayctl.api.client import XrayClient
from xrayctl.workflows.violations import cve_lookup, list_violations


@pytest.fixture
def mock_client() -> MagicMock:
    c = MagicMock(spec=XrayClient)
    c.project = None
    return c


# ---------------------------------------------------------------------------
# list_violations — validation
# ---------------------------------------------------------------------------

def test_list_violations_raises_on_limit_below_1(mock_client: MagicMock) -> None:
    with pytest.raises(ValueError, match="--limit"):
        list_violations(mock_client, limit=0)


# ---------------------------------------------------------------------------
# list_violations — single page
# ---------------------------------------------------------------------------

def test_list_violations_single_page_returns_structured_dict(mock_client: MagicMock) -> None:
    api_response = {
        "violations": [{"id": "v-1", "severity": "High"}],
        "total_violations": 1,
    }
    with patch("xrayctl.api.violations.list_violations", return_value=api_response):
        result = list_violations(mock_client, limit=25)
    assert result["ok"] is True
    assert result["total_violations"] == 1
    assert result["violations"] == [{"id": "v-1", "severity": "High"}]


def test_list_violations_passes_filters_to_api(mock_client: MagicMock) -> None:
    api_response = {"violations": [], "total_violations": 0}
    with patch("xrayctl.api.violations.list_violations", return_value=api_response) as mock_api:
        list_violations(
            mock_client,
            watch="my-watch",
            severities=["Critical", "High"],
            cve="CVE-2024-9999",
            created_from="2024-01-01T00:00:00Z",
            created_to="2024-12-31T23:59:59Z",
        )
    _, kwargs = mock_api.call_args
    f = kwargs["filters"]
    assert f["watch_name"] == "my-watch"
    assert f["severities"] == ["Critical", "High"]
    assert f["cve"] == "CVE-2024-9999"
    assert f["created_from"] == "2024-01-01T00:00:00Z"
    assert f["created_to"] == "2024-12-31T23:59:59Z"


# ---------------------------------------------------------------------------
# list_violations — fetch_all pagination
# ---------------------------------------------------------------------------

def test_list_violations_fetch_all_combines_pages(mock_client: MagicMock) -> None:
    pages = [
        {"violations": [{"id": "v-1"}, {"id": "v-2"}], "total_violations": 3},
        {"violations": [{"id": "v-3"}], "total_violations": 3},
    ]
    with patch("xrayctl.api.violations.list_violations", side_effect=pages):
        result = list_violations(mock_client, limit=2, fetch_all=True)
    assert result["ok"] is True
    assert result["total_violations"] == 3
    assert len(result["violations"]) == 3
    assert result["violations"][2]["id"] == "v-3"


def test_list_violations_fetch_all_stops_on_empty_batch(mock_client: MagicMock) -> None:
    pages = [
        {"violations": [{"id": "v-1"}], "total_violations": 10},
        {"violations": [], "total_violations": 10},
    ]
    with patch("xrayctl.api.violations.list_violations", side_effect=pages):
        result = list_violations(mock_client, limit=5, fetch_all=True)
    assert len(result["violations"]) == 1


# ---------------------------------------------------------------------------
# cve_lookup
# ---------------------------------------------------------------------------

def test_cve_lookup_passes_cve_to_list_violations(mock_client: MagicMock) -> None:
    with patch(
        "xrayctl.workflows.violations.list_violations",
        return_value={"ok": True, "total_violations": 0, "violations": []},
    ) as mock_list:
        cve_lookup(mock_client, cve_id="CVE-2024-1234", limit=10, fetch_all=True)
    _, kwargs = mock_list.call_args
    assert kwargs["cve"] == "CVE-2024-1234"
    assert kwargs["limit"] == 10
    assert kwargs["fetch_all"] is True
