from __future__ import annotations

from typing import Any, Dict
from xrayctl.api.client import XrayClient


def scan_artifact(client: XrayClient, component_id: str) -> Any:
    """
    Trigger an on-demand scan for an artifact using its component ID.

    Args:
        client: Initialized XrayClient.
        component_id: Xray component identifier.

    Returns:
        API response indicating scan initiation.
    """
    # Triggers an on-demand scan using componentID
    payload = {"componentID": component_id}
    return client.request("POST", "/xray/api/v1/scanArtifact", json_body=payload)


def artifact_status(client: XrayClient, *, repo: str, path: str) -> Any:
    """
    Retrieve scan status for a specific artifact.

    Args:
        client: Initialized XrayClient.
        repo: Repository key.
        path: Artifact path within the repository.

    Returns:
        API response containing scan status details.
    """
    # Checks scan status for an artifact by repo/path
    payload: Dict[str, Any] = {"repo": repo, "path": path}
    if client.project:
        payload["project"] = client.project
    return client.request("POST", "/xray/api/v1/artifact/status", json_body=payload)
