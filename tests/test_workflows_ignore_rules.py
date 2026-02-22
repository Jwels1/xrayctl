from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from xrayctl.api.client import XrayClient
from xrayctl.workflows.ignore_rules import _resolve_artifact_name_version, build_payload, create, get_ignore_rule, list_rules


@pytest.fixture
def mock_client() -> MagicMock:
    c = MagicMock(spec=XrayClient)
    c.project = None
    return c


# ---------------------------------------------------------------------------
# build_payload
# ---------------------------------------------------------------------------

def test_build_payload_raises_on_empty_note() -> None:
    with pytest.raises(ValueError, match="note"):
        build_payload(note="", watches=["w"], cves=[], vulns=[], licenses=[], expires_at=None)


def test_build_payload_raises_on_whitespace_note() -> None:
    with pytest.raises(ValueError, match="note"):
        build_payload(note="   ", watches=["w"], cves=[], vulns=[], licenses=[], expires_at=None)


def test_build_payload_raises_when_no_filters() -> None:
    with pytest.raises(ValueError, match="at least one filter"):
        build_payload(note="valid note", watches=[], cves=[], vulns=[], licenses=[], expires_at=None)


def test_build_payload_with_cves() -> None:
    payload = build_payload(
        note="test note", watches=[], cves=["CVE-2024-1234"], vulns=[], licenses=[], expires_at=None
    )
    assert payload["notes"] == "test note"
    assert payload["ignore_filters"]["cves"] == ["CVE-2024-1234"]
    assert "vulnerabilities" not in payload["ignore_filters"]


def test_build_payload_with_all_filters() -> None:
    payload = build_payload(
        note="all filters",
        watches=["watch-1"],
        cves=["CVE-2024-0001"],
        vulns=["XRAY-123"],
        licenses=["MIT"],
        expires_at=None,
    )
    f = payload["ignore_filters"]
    assert f["watches"] == ["watch-1"]
    assert f["cves"] == ["CVE-2024-0001"]
    assert f["vulnerabilities"] == ["XRAY-123"]
    assert f["licenses"] == ["MIT"]


def test_build_payload_includes_expires_at() -> None:
    payload = build_payload(
        note="expiring rule",
        watches=["w"],
        cves=[],
        vulns=[],
        licenses=[],
        expires_at="2026-01-01T00:00:00Z",
    )
    assert payload["expires_at"] == "2026-01-01T00:00:00Z"


def test_build_payload_omits_expires_at_when_none() -> None:
    payload = build_payload(
        note="no expiry", watches=["w"], cves=[], vulns=[], licenses=[], expires_at=None
    )
    assert "expires_at" not in payload


def test_build_payload_artifact_all_fields() -> None:
    payload = build_payload(
        note="artifact rule",
        watches=[],
        cves=[],
        vulns=[],
        licenses=[],
        expires_at=None,
        artifact_name="my-artifact",
        artifact_version="1.0.0",
        artifact_path="my-repo/path/to/artifact",
    )
    artifact = payload["ignore_filters"]["artifact"]
    assert artifact == [{"name": "my-artifact", "version": "1.0.0", "path": "my-repo/path/to/artifact"}]


def test_build_payload_artifact_name_only() -> None:
    payload = build_payload(
        note="artifact rule partial",
        watches=[],
        cves=[],
        vulns=[],
        licenses=[],
        expires_at=None,
        artifact_name="my-artifact",
    )
    artifact = payload["ignore_filters"]["artifact"]
    assert artifact == [{"name": "my-artifact"}]
    assert "version" not in artifact[0]
    assert "path" not in artifact[0]


def test_build_payload_artifact_raises_when_version_without_name() -> None:
    with pytest.raises(ValueError, match="--artifact-name is required"):
        build_payload(
            note="missing name",
            watches=[],
            cves=[],
            vulns=[],
            licenses=[],
            expires_at=None,
            artifact_version="1.0.0",
        )


def test_build_payload_artifact_raises_when_path_without_name() -> None:
    with pytest.raises(ValueError, match="--artifact-name is required"):
        build_payload(
            note="missing name",
            watches=[],
            cves=[],
            vulns=[],
            licenses=[],
            expires_at=None,
            artifact_path="my-repo/path/to/artifact",
        )


def test_build_payload_artifact_alone_satisfies_filter_requirement() -> None:
    payload = build_payload(
        note="artifact only",
        watches=[],
        cves=[],
        vulns=[],
        licenses=[],
        expires_at=None,
        artifact_name="my-artifact",
    )
    assert "artifact" in payload["ignore_filters"]


def test_build_payload_raises_when_no_filters_including_artifact() -> None:
    with pytest.raises(ValueError, match="at least one filter"):
        build_payload(
            note="no filters",
            watches=[],
            cves=[],
            vulns=[],
            licenses=[],
            expires_at=None,
        )


# ---------------------------------------------------------------------------
# _resolve_artifact_name_version
# ---------------------------------------------------------------------------

def test_resolve_npm_properties() -> None:
    name, version = _resolve_artifact_name_version(
        {"properties": {"npm.name": ["my-pkg"], "npm.version": ["2.0.0"]}}
    )
    assert name == "my-pkg"
    assert version == "2.0.0"


def test_resolve_pypi_properties() -> None:
    name, version = _resolve_artifact_name_version(
        {"properties": {"pypi.name": ["requests"], "pypi.version": ["2.31.0"]}}
    )
    assert name == "requests"
    assert version == "2.31.0"


def test_resolve_maven_properties() -> None:
    name, version = _resolve_artifact_name_version(
        {"properties": {"maven.artifactId": ["my-lib"], "maven.version": ["1.0.0"]}}
    )
    assert name == "my-lib"
    assert version == "1.0.0"


def test_resolve_first_name_key_wins() -> None:
    # npm.name and pypi.name both present — npm.name is earlier in the list
    name, version = _resolve_artifact_name_version(
        {"properties": {"pypi.name": ["pypi-pkg"], "npm.name": ["npm-pkg"], "npm.version": ["1.0.0"]}}
    )
    assert name == "npm-pkg"


def test_resolve_version_none_when_no_version_property() -> None:
    name, version = _resolve_artifact_name_version(
        {"properties": {"npm.name": ["my-pkg"]}}
    )
    assert name == "my-pkg"
    assert version is None


def test_resolve_raises_when_no_name_property() -> None:
    with pytest.raises(ValueError, match="_PROPERTY_NAME_KEYS"):
        _resolve_artifact_name_version({"properties": {"some.other.prop": ["value"]}})


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------

def test_create_dry_run_does_not_call_api(mock_client: MagicMock) -> None:
    with patch("xrayctl.api.ignore_rules.create_ignore_rule") as mock_api:
        result = create(
            mock_client,
            note="dry run test",
            watches=["my-watch"],
            cves=[],
            vulns=[],
            licenses=[],
            expires_at=None,
            dry_run=True,
        )
    mock_api.assert_not_called()
    assert result["ok"] is True
    assert "request" in result
    assert "response" not in result


def test_create_resolves_artifact_name_version_from_path(mock_client: MagicMock) -> None:
    properties_resp = {"properties": {"npm.name": ["my-pkg"], "npm.version": ["2.0.0"]}}
    with patch("xrayctl.api.artifactory.get_artifact_properties", return_value=properties_resp), \
         patch("xrayctl.api.ignore_rules.create_ignore_rule", return_value={"id": "rule-1"}):
        result = create(
            mock_client,
            note="auto-resolved",
            watches=[],
            cves=[],
            vulns=[],
            licenses=[],
            expires_at=None,
            dry_run=True,
            artifact_path="my-repo/my-pkg/2.0.0",
        )
    artifact = result["request"]["ignore_filters"]["artifact"][0]
    assert artifact["name"] == "my-pkg"
    assert artifact["version"] == "2.0.0"
    assert artifact["path"] == "my-repo/my-pkg/2.0.0"


def test_create_does_not_call_artifactory_when_name_provided(mock_client: MagicMock) -> None:
    with patch("xrayctl.api.artifactory.get_artifact_properties") as mock_props, \
         patch("xrayctl.api.ignore_rules.create_ignore_rule", return_value={}):
        create(
            mock_client,
            note="name provided",
            watches=[],
            cves=[],
            vulns=[],
            licenses=[],
            expires_at=None,
            dry_run=True,
            artifact_name="explicit-name",
            artifact_path="my-repo/my-pkg/2.0.0",
        )
    mock_props.assert_not_called()


def test_create_calls_api_and_returns_response(mock_client: MagicMock) -> None:
    with patch(
        "xrayctl.api.ignore_rules.create_ignore_rule",
        return_value={"id": "new-rule-id"},
    ) as mock_api:
        result = create(
            mock_client,
            note="real create",
            watches=["my-watch"],
            cves=[],
            vulns=[],
            licenses=[],
            expires_at=None,
            dry_run=False,
        )
    mock_api.assert_called_once()
    assert result["ok"] is True
    assert result["response"] == {"id": "new-rule-id"}


# ---------------------------------------------------------------------------
# list_rules
# ---------------------------------------------------------------------------

def test_list_rules_raises_when_page_below_1(mock_client: MagicMock) -> None:
    with pytest.raises(ValueError, match="--page"):
        list_rules(
            mock_client,
            watch=None, policy=None, vulnerability=None, cve=None,
            license_name=None, component_name=None, component_version=None,
            page=0, rows=50, order_by=None, direction=None,
            expires_before=None, expires_after=None, fetch_all=False,
        )


def test_list_rules_raises_when_rows_below_1(mock_client: MagicMock) -> None:
    with pytest.raises(ValueError, match="--rows"):
        list_rules(
            mock_client,
            watch=None, policy=None, vulnerability=None, cve=None,
            license_name=None, component_name=None, component_version=None,
            page=1, rows=0, order_by=None, direction=None,
            expires_before=None, expires_after=None, fetch_all=False,
        )


def test_list_rules_single_page(mock_client: MagicMock) -> None:
    api_response = {"data": [{"id": "rule-1"}], "total_count": 1}
    with patch("xrayctl.api.ignore_rules.get_ignore_rules", return_value=api_response):
        result = list_rules(
            mock_client,
            watch=None, policy=None, vulnerability=None, cve=None,
            license_name=None, component_name=None, component_version=None,
            page=1, rows=50, order_by=None, direction=None,
            expires_before=None, expires_after=None, fetch_all=False,
        )
    assert result["ok"] is True
    assert result["response"] == api_response


def test_list_rules_fetch_all_paginates_by_total_count(mock_client: MagicMock) -> None:
    pages = [
        {"data": [{"id": "rule-1"}, {"id": "rule-2"}], "total_count": 3},
        {"data": [{"id": "rule-3"}], "total_count": 3},
    ]
    with patch("xrayctl.api.ignore_rules.get_ignore_rules", side_effect=pages):
        result = list_rules(
            mock_client,
            watch=None, policy=None, vulnerability=None, cve=None,
            license_name=None, component_name=None, component_version=None,
            page=1, rows=2, order_by=None, direction=None,
            expires_before=None, expires_after=None, fetch_all=True,
        )
    assert result["ok"] is True
    assert len(result["response"]["data"]) == 3
    assert result["response"]["total_count"] == 3


def test_list_rules_fetch_all_stops_on_empty_data(mock_client: MagicMock) -> None:
    pages = [
        {"data": [{"id": "rule-1"}]},
        {"data": []},
    ]
    with patch("xrayctl.api.ignore_rules.get_ignore_rules", side_effect=pages):
        result = list_rules(
            mock_client,
            watch=None, policy=None, vulnerability=None, cve=None,
            license_name=None, component_name=None, component_version=None,
            page=1, rows=10, order_by=None, direction=None,
            expires_before=None, expires_after=None, fetch_all=True,
        )
    assert len(result["response"]["data"]) == 1


# ---------------------------------------------------------------------------
# get_ignore_rule
# ---------------------------------------------------------------------------

def test_get_ignore_rule_delegates_to_api(mock_client: MagicMock) -> None:
    api_response = {"id": "abc", "notes": "test rule"}
    with patch("xrayctl.api.ignore_rules.get_ignore_rule", return_value=api_response) as mock_api:
        result = get_ignore_rule(mock_client, "abc")
    mock_api.assert_called_once_with(mock_client, "abc")
    assert result == api_response
