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
    """
    Retrieve repositories known to Xray (paged).

    Args:
        client: Initialized XrayClient.
        offset: Pagination offset returned by previous response.
        num_of_rows: Number of repositories per page.
        search: Optional search string to filter repo names.

    Returns:
        API response containing repository metadata and paging info.
    """
    params: Dict[str, Any] = {
        "offset": offset,
        "num_of_rows": num_of_rows,
    }
    if search:
        params["search"] = search

    return client.request("GET", "/xray/api/v1/repos", params=params)
