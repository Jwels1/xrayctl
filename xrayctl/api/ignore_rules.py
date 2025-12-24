from __future__ import annotations
from typing import Any, Dict
from xrayctl.api.client import XrayClient


def create_ignore_rule(client: XrayClient, payload: Dict[str, Any]) -> Any:
    params = {}
    if client.project:
        params["projectKey"] = client.project
    return client.request("POST", "/xray/api/v1/ignore_rules", json_body=payload, params=params)
