from __future__ import annotations
from typing import Any, Dict, Optional
from xrayctl.api.client import XrayClient


def create_ignore_rule(client: XrayClient, payload: Dict[str, Any]) -> Any:
    params = {}
    if client.project:
        params["projectKey"] = client.project
    return client.request("POST", "/xray/api/v1/ignore_rules", json_body=payload, params=params)


def get_ignore_rules(client: XrayClient, params: Optional[Dict[str, Any]] = None) -> Any:
    # For project-scoped usage, Xray supports projectKey as a query parameter. :contentReference[oaicite:4]{index=4}
    q = dict(params or {})
    if client.project and "projectKey" not in q:
        q["projectKey"] = client.project

    return client.request("GET", "/xray/api/v1/ignore_rules", params=q)


def get_ignore_rule(client: XrayClient, rule_id: str) -> Any:
    params: Optional[Dict[str, Any]] = None
    if client.project:
        params = {"projectKey": client.project}
    # Usage: GET /xray/api/v1/ignore_rules/{id} :contentReference[oaicite:1]{index=1}
    return client.request("GET", f"/xray/api/v1/ignore_rules/{rule_id}", params=params)
