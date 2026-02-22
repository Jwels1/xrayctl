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
    """
    Retrieve artifacts from a specific repository (paged).

    Args:
        client: Initialized XrayClient.
        repo: Repository key to list artifacts from.
        offset: Pagination offset returned by previous response.
        num_of_rows: Number of artifacts per page.

    Returns:
        API response containing artifact metadata and paging info.
    """
    params: Dict[str, Any] = {
        "repo": repo,
        "offset": offset,
        "num_of_rows": num_of_rows,
    }
    return client.request("GET", "/xray/api/v1/artifacts", params=params)
