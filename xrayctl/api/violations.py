from __future__ import annotations

from typing import Any, Dict, Optional

from xrayctl.api.client import XrayClient


def list_violations(
    client: XrayClient,
    *,
    filters: Optional[Dict[str, Any]] = None,
    order_by: str = "created",
    direction: str = "asc",
    limit: int = 25,
    offset: int = 0,
) -> Any:
    """
    List violations from the Xray violations API.

    Args:
        client: Initialized XrayClient.
        filters: Optional filters dict (watch, component, artifact, etc.).
        order_by: Field to sort by.
        direction: Sort direction ('asc' or 'desc').
        limit: Number of results per page.
        offset: Offset for pagination.

    Returns:
        API response containing violations list and total count.
    """
    params: Dict[str, Any] = {}
    if client.project:
        params["projectKey"] = client.project

    body: Dict[str, Any] = {
        "filters": filters or {},
        "pagination": {
            "order_by": order_by,
            "direction": direction,
            "limit": limit,
            "offset": offset,
        },
    }

    return client.request(
        "POST",
        "/xray/api/v1/violations",
        json_body=body,
        params=params or None,
    )
