from __future__ import annotations
from typing import Any, Dict, List, Optional

from xrayctl.api.client import XrayClient
from xrayctl.api import ignore_rules as ignore_api


def build_payload(
    *,
    note: str,
    watches: List[str],
    cves: List[str],
    vulns: List[str],
    licenses: List[str],
    expires_at: Optional[str]
) -> Dict[str, Any]:
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

    if not ignore_filters:
        raise ValueError("Provide at least one filter: --watch/--cve/--vuln/--license")

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
    dry_run: Optional[bool]
) -> Dict[str, Any]:
    payload = build_payload(
        note=note,
        watches=watches,
        cves=cves,
        vulns=vulns,
        licenses=licenses,
        expires_at=expires_at,
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
    params: Optional[Dict[str, Any]] = None
    if client.project:
        params = {"projectKey": client.project}
    # Usage: GET /xray/api/v1/ignore_rules/{id} :contentReference[oaicite:1]{index=1}
    return client.request("GET", f"/xray/api/v1/ignore_rules/{rule_id}", params=params)
