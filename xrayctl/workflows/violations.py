from __future__ import annotations

from typing import Any, Dict, List, Optional

from xrayctl.api.client import XrayClient
from xrayctl.api import violations as violations_api


def list_violations(
    client: XrayClient,
    *,
    watch: Optional[str] = None,
    severities: Optional[List[str]] = None,
    cve: Optional[str] = None,
    created_from: Optional[str] = None,
    created_to: Optional[str] = None,
    limit: int = 25,
    order_by: str = "created",
    direction: str = "asc",
    fetch_all: bool = False,
) -> Dict[str, Any]:
    """
    List violations with optional filters and pagination.

    Args:
        client: Initialized XrayClient.
        watch: Filter by watch name.
        severities: Filter by severity levels (e.g. ['Critical', 'High']).
        cve: Filter by CVE identifier.
        created_from: ISO8601 UTC lower bound for creation date.
        created_to: ISO8601 UTC upper bound for creation date.
        limit: Number of results per page.
        order_by: Field to sort by.
        direction: Sort direction ('asc' or 'desc').
        fetch_all: If True, auto-paginate and return all results.

    Returns:
        Structured result with ok flag, total_violations count, and violations list.

    Raises:
        ValueError: If limit is less than 1.
    """
    if limit < 1:
        raise ValueError("--limit must be >= 1")

    filters: Dict[str, Any] = {}
    if watch:
        filters["watch_name"] = watch
    if severities:
        filters["severities"] = severities
    if cve:
        filters["cve"] = cve
    if created_from:
        filters["created_from"] = created_from
    if created_to:
        filters["created_to"] = created_to

    if not fetch_all:
        resp = violations_api.list_violations(
            client,
            filters=filters,
            order_by=order_by,
            direction=direction,
            limit=limit,
            offset=0,
        )
        violations = resp.get("violations", []) if isinstance(resp, dict) else []
        total = resp.get("total_violations", len(violations)) if isinstance(resp, dict) else len(violations)
        return {"ok": True, "total_violations": total, "violations": violations}

    # Auto-paginate: keep fetching until we have all results
    all_violations: List[Any] = []
    offset = 0
    total_violations: Optional[int] = None

    while True:
        resp = violations_api.list_violations(
            client,
            filters=filters,
            order_by=order_by,
            direction=direction,
            limit=limit,
            offset=offset,
        )

        batch = resp.get("violations", []) if isinstance(resp, dict) else []
        all_violations.extend(batch)

        if isinstance(resp, dict):
            total_violations = resp.get("total_violations", total_violations)

        if not batch:
            break

        if total_violations is not None and len(all_violations) >= int(total_violations):
            break

        offset += limit

    return {
        "ok": True,
        "total_violations": total_violations if total_violations is not None else len(all_violations),
        "violations": all_violations,
    }


def cve_lookup(
    client: XrayClient,
    *,
    cve_id: str,
    limit: int = 25,
    order_by: str = "created",
    direction: str = "asc",
    fetch_all: bool = False,
) -> Dict[str, Any]:
    """
    Look up violations for a specific CVE identifier.

    Args:
        client: Initialized XrayClient.
        cve_id: CVE identifier (e.g. 'CVE-2024-1234').
        limit: Number of results per page.
        order_by: Field to sort by.
        direction: Sort direction ('asc' or 'desc').
        fetch_all: If True, auto-paginate and return all results.

    Returns:
        Structured result with ok flag, total_violations count, and violations list.
    """
    return list_violations(
        client,
        cve=cve_id,
        limit=limit,
        order_by=order_by,
        direction=direction,
        fetch_all=fetch_all,
    )
