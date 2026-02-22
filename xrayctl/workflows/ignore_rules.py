from __future__ import annotations
from typing import Any, Dict, List, Optional

from xrayctl.api.client import XrayClient
from xrayctl.api import ignore_rules as ignore_api
from xrayctl.api import artifactory as artifactory_api

# Maps Artifactory package-type property keys to (name_key, version_key).
# Values are lists so the first populated key wins.
# Add entries here when you encounter a package type not yet covered.
_PROPERTY_NAME_KEYS: list[str] = [
    "npm.name",
    "pypi.name",
    "maven.artifactId",
    "nuget.id",
    "helm.name",
    "deb.name",
    "rpm.metadata.name",
    "gem.name",
    "bower.name",
]

_PROPERTY_VERSION_KEYS: list[str] = [
    "npm.version",
    "pypi.version",
    "maven.version",
    "nuget.version",
    "helm.version",
    "deb.version",
    "rpm.metadata.version",
    "gem.version",
    "bower.version",
]


def _resolve_artifact_name_version(
    properties_resp: Any,
) -> tuple[str, Optional[str]]:
    """
    Extract artifact name and version from an Artifactory properties API response.

    Tries each key in _PROPERTY_NAME_KEYS / _PROPERTY_VERSION_KEYS in order and
    returns the first populated value. To support additional package types, add
    entries to those module-level lists.

    Args:
        properties_resp: Response dict from GET /artifactory/api/storage/{path}?properties.

    Returns:
        Tuple of (name, version). Version is None when no version property is found.

    Raises:
        ValueError: If no recognised name property is present in the response.
    """
    props: dict[str, list[str]] = (
        properties_resp.get("properties", {}) if isinstance(properties_resp, dict) else {}
    )

    name: Optional[str] = None
    for key in _PROPERTY_NAME_KEYS:
        values = props.get(key)
        if values:
            name = values[0]
            break

    if not name:
        raise ValueError(
            f"Could not determine artifact name from properties: {list(props.keys())}. "
            "Add the relevant property key to _PROPERTY_NAME_KEYS in workflows/ignore_rules.py."
        )

    version: Optional[str] = None
    for key in _PROPERTY_VERSION_KEYS:
        values = props.get(key)
        if values:
            version = values[0]
            break

    return name, version


def build_payload(
    *,
    note: str,
    watches: List[str],
    cves: List[str],
    vulns: List[str],
    licenses: List[str],
    expires_at: Optional[str],
    artifact_name: Optional[str] = None,
    artifact_version: Optional[str] = None,
    artifact_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build the request payload for creating an ignore rule.

    Args:
        note: Human-readable reason for the ignore rule.
        watches: Watch names to scope the rule.
        cves: CVE identifiers.
        vulns: Xray vulnerability identifiers.
        licenses: License names or 'any'.
        expires_at: Optional expiration timestamp (ISO8601).
        artifact_name: Artifact name to scope the rule to.
        artifact_version: Artifact version to scope the rule to.
        artifact_path: Artifact repo path to scope the rule to.

    Returns:
        Ignore rule payload.

    Raises:
        ValueError: If no ignore filters are provided.
    """
    if not note.strip():
        raise ValueError("--note must not be empty")

    ignore_filters: Dict[str, Any] = {}

    if watches:
        ignore_filters["watches"] = watches
    if cves:
        ignore_filters["cves"] = cves
    if vulns:
        ignore_filters["vulnerabilities"] = vulns
    if licenses:
        ignore_filters["licenses"] = licenses

    artifact: Dict[str, str] = {}
    if artifact_version or artifact_path:
        if not artifact_name:
            raise ValueError("--artifact-name is required when using --artifact-version or --artifact-path")
    if artifact_name:
        artifact["name"] = artifact_name
    if artifact_version:
        artifact["version"] = artifact_version
    if artifact_path:
        artifact["path"] = artifact_path
    if artifact:
        ignore_filters["artifact"] = [artifact]

    if not ignore_filters:
        raise ValueError("Provide at least one filter: --watch/--cve/--vuln/--license/--artifact-*")

    payload: Dict[str, Any] = {"notes": note, "ignore_filters": ignore_filters}
    if expires_at:
        payload["expires_at"] = expires_at

    return payload


def create(
    client: XrayClient,
    *,
    note: str,
    watches: List[str],
    cves: List[str],
    vulns: List[str],
    licenses: List[str],
    expires_at: Optional[str],
    dry_run: Optional[bool],
    artifact_name: Optional[str] = None,
    artifact_version: Optional[str] = None,
    artifact_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create an ignore rule via Xray.

    Args:
        client: Initialized XrayClient.
        note: Reason for ignore rule.
        watches: Watch names.
        cves: CVE identifiers.
        vulns: Vulnerability identifiers.
        licenses: License names.
        expires_at: Optional expiration timestamp.
        artifact_name: Artifact name to scope the rule to.
        artifact_version: Artifact version to scope the rule to.
        artifact_path: Artifact repo path to scope the rule to.

    Returns:
        Structured result containing request and response.
    """
    if artifact_path and not artifact_name:
        info = artifactory_api.get_artifact_properties(client, artifact_path)
        resolved_name, resolved_version = _resolve_artifact_name_version(info)
        artifact_name = resolved_name
        if artifact_version is None:
            artifact_version = resolved_version

    payload = build_payload(
        note=note,
        watches=watches,
        cves=cves,
        vulns=vulns,
        licenses=licenses,
        expires_at=expires_at,
        artifact_name=artifact_name,
        artifact_version=artifact_version,
        artifact_path=artifact_path,
    )
    if dry_run:
        return {"ok": True, "request": payload}
        
    else:
        resp = ignore_api.create_ignore_rule(client, payload)
        return {"ok": True, "request": payload, "response": resp}


def _build_list_params(
    *,
    watch: Optional[str],
    policy: Optional[str],
    vulnerability: Optional[str],
    cve: Optional[str],
    license_name: Optional[str],
    component_name: Optional[str],
    component_version: Optional[str],
    page: int,
    rows: int,
    order_by: Optional[str],
    direction: Optional[str],
    expires_before: Optional[str],
    expires_after: Optional[str],
) -> Dict[str, Any]:
    # These parameter names match the REST API docs. :contentReference[oaicite:5]{index=5}
    params: Dict[str, Any] = {
        "page_num": page,
        "num_of_rows": rows,
    }

    if order_by:
        params["order_by"] = order_by
    if direction:
        params["direction"] = direction

    if watch:
        params["watch"] = watch
    if policy:
        params["policy"] = policy
    if vulnerability:
        params["vulnerability"] = vulnerability
    if cve:
        params["cve"] = cve
    if license_name:
        params["license"] = license_name

    if component_name:
        params["component_name"] = component_name
    if component_version:
        params["component_version"] = component_version

    if expires_before:
        params["expires_before"] = expires_before
    if expires_after:
        params["expires_after"] = expires_after

    return params


def list_rules(
    client: XrayClient,
    *,
    watch: Optional[str],
    policy: Optional[str],
    vulnerability: Optional[str],
    cve: Optional[str],
    license_name: Optional[str],
    component_name: Optional[str],
    component_version: Optional[str],
    page: int,
    rows: int,
    order_by: Optional[str],
    direction: Optional[str],
    expires_before: Optional[str],
    expires_after: Optional[str],
    fetch_all: bool,
) -> Dict[str, Any]:
    """
    List ignore rules with optional filtering and pagination.

    Args:
        client: Initialized XrayClient.
        watch: Filter by watch name.
        policy: Filter by policy name.
        vulnerability: Filter by vulnerability id.
        cve: Filter by CVE id.
        license_name: Filter by license name.
        component_name: Filter by component name.
        component_version: Filter by component version.
        page: Page number (1-based).
        rows: Rows per page.
        order_by: Field to order by.
        direction: Sort direction ('asc' or 'desc').
        expires_before: Filter rules expiring before this timestamp.
        expires_after: Filter rules expiring after this timestamp.
        fetch_all: If True, auto-paginate and return all results.

    Returns:
        Structured result containing params and response data.
    """
    if page < 1:
        raise ValueError("--page must be >= 1")
    if rows < 1:
        raise ValueError("--rows must be >= 1")

    params = _build_list_params(
        watch=watch,
        policy=policy,
        vulnerability=vulnerability,
        cve=cve,
        license_name=license_name,
        component_name=component_name,
        component_version=component_version,
        page=page,
        rows=rows,
        order_by=order_by,
        direction=direction,
        expires_before=expires_before,
        expires_after=expires_after,
    )

    if not fetch_all:
        resp = ignore_api.get_ignore_rules(client, params=params)
        return {"ok": True, "params": params, "response": resp}

    # Auto-paginate: keep requesting pages until we collected total_count
    all_data: List[Any] = []
    current_page = page
    total_count = None

    while True:
        params["page_num"] = current_page
        resp = ignore_api.get_ignore_rules(client, params=params)

        data = resp.get("data", []) if isinstance(resp, dict) else []
        all_data.extend(data)

        if isinstance(resp, dict):
            total_count = resp.get("total_count", total_count)

        if total_count is None:
            # No total_count -> stop when the page is empty
            if not data:
                break
        else:
            if len(all_data) >= int(total_count):
                break

        if not data:
            break

        current_page += 1

    return {
        "ok": True,
        "params": params,
        "response": {"data": all_data, "total_count": total_count if total_count is not None else len(all_data)},
    }


def get_ignore_rule(client: XrayClient, rule_id: str) -> Any:
    """
    Retrieve a single ignore rule and normalize output.

    Args:
        client: Initialized XrayClient.
        rule_id: Ignore rule identifier.

    Returns:
        Structured ignore rule response.
    """
    return ignore_api.get_ignore_rule(client, rule_id)
