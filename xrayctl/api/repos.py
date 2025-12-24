from __future__ import annotations
from typing import Any, Dict, Optional
from xrayctl.api.client import XrayClient


def list_repos(
    client: XrayClient,
    *,
    offset: int = 0,
    num_of_rows: int = 200,
    search: Optional[str] = None,
) -> Any:
    params: Dict[str, Any] = {
        "offset": offset,
        "num_of_rows": num_of_rows,
    }
    if search:
        params["search"] = search

    return client.request("GET", "/xray/api/v1/repos", params=params)
