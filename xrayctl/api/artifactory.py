from __future__ import annotations

from typing import Any

from xrayctl.api.client import XrayClient


def get_artifact_properties(client: XrayClient, path: str) -> Any:
    """
    Get all properties attached to an artifact in Artifactory.

    Args:
        client: Initialized XrayClient.
        path: Full path including repo key (e.g. 'my-repo/path/to/artifact').

    Returns:
        Dict with a 'properties' key mapping property names to lists of values.
    """
    return client.request("GET", f"/artifactory/api/storage/{path.lstrip('/')}?properties")
