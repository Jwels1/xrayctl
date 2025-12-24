from __future__ import annotations

import time
from typing import Any, Dict, Optional

from xrayctl.api.client import XrayClient
from xrayctl.api import scans as scans_api


# These are common terminal-ish values; if your instance returns different ones,
# you can tweak without touching API code.
_TERMINAL = {"DONE", "FAILED", "PARTIAL", "NOT_SUPPORTED"}


def scan_artifact(
    client: XrayClient,
    *,
    component_id: str,
    wait: bool,
    repo: Optional[str],
    path: Optional[str],
    poll_seconds: int,
    timeout_seconds: int,
) -> Dict[str, Any]:
    if not component_id.strip():
        raise ValueError("--component-id must not be empty")

    if poll_seconds < 1:
        raise ValueError("--poll-seconds must be >= 1")
    if timeout_seconds < 1:
        raise ValueError("--timeout-seconds must be >= 1")

    # 1) Trigger scan
    start_resp = scans_api.scan_artifact(client, component_id)

    # 2) If not waiting, return immediately
    if not wait:
        return {
            "ok": True,
            "type": "artifact",
            "component_id": component_id,
            "started": start_resp,
        }

    # 3) Waiting requires repo+path (status API needs them)
    if not repo or not path:
        raise ValueError("--wait requires --repo and --path (artifact status API uses repo/path, not component-id)")

    deadline = time.time() + timeout_seconds
    last_status = None
    last_resp = None

    while time.time() < deadline:
        status_resp = scans_api.artifact_status(client, repo=repo, path=path)
        last_resp = status_resp

        # Different Xray versions may shape this differently; we try a couple common patterns.
        # If you see your instance returns something else, we can adjust here.
        if isinstance(status_resp, dict):
            overall = status_resp.get("overall") or status_resp.get("summary") or {}
            if isinstance(overall, dict):
                last_status = overall.get("status") or overall.get("scan_status") or status_resp.get("status")

        if last_status in _TERMINAL:
            return {
                "ok": last_status == "DONE",
                "type": "artifact",
                "component_id": component_id,
                "artifact": {"repo": repo, "path": path, "project": client.project},
                "started": start_resp,
                "final_status": last_status,
                "status": status_resp,
            }

        time.sleep(poll_seconds)

    return {
        "ok": False,
        "type": "artifact",
        "component_id": component_id,
        "artifact": {"repo": repo, "path": path, "project": client.project},
        "started": start_resp,
        "final_status": last_status,
        "status": last_resp,
        "error": f"Timed out after {timeout_seconds}s waiting for artifact scan to complete",
    }
