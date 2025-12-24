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
    
