from __future__ import annotations
from typing import Any, Dict
from xrayctl.api.client import XrayClient


def list_artifacts(
    client: XrayClient,
    *,
    repo: str,
    offset: int = 0,
    num_of_rows: int = 200,
) -> Any:
    params: Dict[str, Any] = {
        "repo": repo,
        "offset": offset,
        "num_of_rows": num_of_rows,
    }
    return client.request("GET", "/xray/api/v1/artifacts", params=params)
