"""Tests for all thin API wrapper modules (system, ignore_rules, artifacts, repos, scans)."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from xrayctl.api import artifacts, ignore_rules, repos, scans, system
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


# ---------------------------------------------------------------------------
# system
# ---------------------------------------------------------------------------

def test_ping_calls_correct_endpoint(mock_client: MagicMock) -> None:
    system.ping(mock_client)
    mock_client.request.assert_called_once_with("GET", "/xray/api/v1/system/ping")


# ---------------------------------------------------------------------------
# ignore_rules
# ---------------------------------------------------------------------------

def test_create_ignore_rule_posts_payload(mock_client: MagicMock) -> None:
    payload = {"notes": "test", "ignore_filters": {"cves": ["CVE-2024-1234"]}}
    ignore_rules.create_ignore_rule(mock_client, payload)
    mock_client.request.assert_called_once_with(
        "POST", "/xray/api/v1/ignore_rules", json_body=payload, params={}
    )


def test_create_ignore_rule_adds_project_key(mock_client_with_project: MagicMock) -> None:
    ignore_rules.create_ignore_rule(mock_client_with_project, {"notes": "t", "ignore_filters": {}})
    _, kwargs = mock_client_with_project.request.call_args
    assert kwargs["params"]["projectKey"] == "my-project"


def test_get_ignore_rules_get_request(mock_client: MagicMock) -> None:
    ignore_rules.get_ignore_rules(mock_client, params={"page_num": 1, "num_of_rows": 50})
    mock_client.request.assert_called_once_with(
        "GET", "/xray/api/v1/ignore_rules",
        params={"page_num": 1, "num_of_rows": 50},
    )


def test_get_ignore_rules_adds_project_key(mock_client_with_project: MagicMock) -> None:
    ignore_rules.get_ignore_rules(mock_client_with_project, params={"page_num": 1})
    _, kwargs = mock_client_with_project.request.call_args
    assert kwargs["params"]["projectKey"] == "my-project"


def test_get_ignore_rules_does_not_overwrite_existing_project_key(mock_client_with_project: MagicMock) -> None:
    ignore_rules.get_ignore_rules(mock_client_with_project, params={"projectKey": "override"})
    _, kwargs = mock_client_with_project.request.call_args
    assert kwargs["params"]["projectKey"] == "override"


def test_get_ignore_rule_by_id(mock_client: MagicMock) -> None:
    ignore_rules.get_ignore_rule(mock_client, "rule-123")
    mock_client.request.assert_called_once_with(
        "GET", "/xray/api/v1/ignore_rules/rule-123", params=None
    )


def test_get_ignore_rule_adds_project_key(mock_client_with_project: MagicMock) -> None:
    ignore_rules.get_ignore_rule(mock_client_with_project, "rule-123")
    _, kwargs = mock_client_with_project.request.call_args
    assert kwargs["params"] == {"projectKey": "my-project"}


# ---------------------------------------------------------------------------
# artifacts
# ---------------------------------------------------------------------------

def test_list_artifacts_passes_params(mock_client: MagicMock) -> None:
    artifacts.list_artifacts(mock_client, repo="my-repo", offset=200, num_of_rows=100)
    mock_client.request.assert_called_once_with(
        "GET", "/xray/api/v1/artifacts",
        params={"repo": "my-repo", "offset": 200, "num_of_rows": 100},
    )


def test_list_artifacts_default_offset_and_rows(mock_client: MagicMock) -> None:
    artifacts.list_artifacts(mock_client, repo="my-repo")
    _, kwargs = mock_client.request.call_args
    assert kwargs["params"]["offset"] == 0
    assert kwargs["params"]["num_of_rows"] == 200


# ---------------------------------------------------------------------------
# repos
# ---------------------------------------------------------------------------

def test_list_repos_passes_offset_and_rows(mock_client: MagicMock) -> None:
    repos.list_repos(mock_client, offset=0, num_of_rows=200)
    mock_client.request.assert_called_once_with(
        "GET", "/xray/api/v1/repos",
        params={"offset": 0, "num_of_rows": 200},
    )


def test_list_repos_omits_search_when_none(mock_client: MagicMock) -> None:
    repos.list_repos(mock_client, offset=0, num_of_rows=200, search=None)
    _, kwargs = mock_client.request.call_args
    assert "search" not in kwargs["params"]


def test_list_repos_includes_search_when_provided(mock_client: MagicMock) -> None:
    repos.list_repos(mock_client, offset=0, num_of_rows=200, search="prod")
    _, kwargs = mock_client.request.call_args
    assert kwargs["params"]["search"] == "prod"


# ---------------------------------------------------------------------------
# scans
# ---------------------------------------------------------------------------

def test_scan_artifact_posts_component_id(mock_client: MagicMock) -> None:
    scans.scan_artifact(mock_client, "docker://alpine:3.20")
    mock_client.request.assert_called_once_with(
        "POST", "/xray/api/v1/scanArtifact",
        json_body={"componentID": "docker://alpine:3.20"},
    )


def test_artifact_status_posts_repo_and_path(mock_client: MagicMock) -> None:
    scans.artifact_status(mock_client, repo="my-repo", path="alpine/3.20")
    mock_client.request.assert_called_once_with(
        "POST", "/xray/api/v1/artifact/status",
        json_body={"repo": "my-repo", "path": "alpine/3.20"},
    )


def test_artifact_status_includes_project_when_set(mock_client_with_project: MagicMock) -> None:
    scans.artifact_status(mock_client_with_project, repo="my-repo", path="alpine/3.20")
    _, kwargs = mock_client_with_project.request.call_args
    assert kwargs["json_body"]["project"] == "my-project"


def test_artifact_status_no_project_when_unset(mock_client: MagicMock) -> None:
    scans.artifact_status(mock_client, repo="my-repo", path="alpine/3.20")
    _, kwargs = mock_client.request.call_args
    assert "project" not in kwargs["json_body"]
