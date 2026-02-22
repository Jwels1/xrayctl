from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from xrayctl.api.client import XrayClient
from xrayctl.workflows.scans import scan_artifact

_COMPONENT_ID = "docker://alpine:3.20"
_REPO = "my-docker-repo"
_PATH = "alpine/3.20"


@pytest.fixture
def mock_client() -> MagicMock:
    c = MagicMock(spec=XrayClient)
    c.project = None
    return c


# ---------------------------------------------------------------------------
# input validation
# ---------------------------------------------------------------------------

def test_scan_artifact_raises_on_empty_component_id(mock_client: MagicMock) -> None:
    with pytest.raises(ValueError, match="component-id"):
        scan_artifact(
            mock_client, component_id="   ", wait=False,
            repo=None, path=None, poll_seconds=5, timeout_seconds=300,
        )


def test_scan_artifact_raises_when_poll_seconds_below_1(mock_client: MagicMock) -> None:
    with pytest.raises(ValueError, match="poll-seconds"):
        scan_artifact(
            mock_client, component_id=_COMPONENT_ID, wait=False,
            repo=None, path=None, poll_seconds=0, timeout_seconds=300,
        )


def test_scan_artifact_raises_when_timeout_seconds_below_1(mock_client: MagicMock) -> None:
    with pytest.raises(ValueError, match="timeout-seconds"):
        scan_artifact(
            mock_client, component_id=_COMPONENT_ID, wait=False,
            repo=None, path=None, poll_seconds=5, timeout_seconds=0,
        )


def test_scan_artifact_wait_requires_repo(mock_client: MagicMock) -> None:
    with patch("xrayctl.api.scans.scan_artifact", return_value={}):
        with pytest.raises(ValueError, match="--wait requires"):
            scan_artifact(
                mock_client, component_id=_COMPONENT_ID, wait=True,
                repo=None, path=_PATH, poll_seconds=5, timeout_seconds=300,
            )


def test_scan_artifact_wait_requires_path(mock_client: MagicMock) -> None:
    with patch("xrayctl.api.scans.scan_artifact", return_value={}):
        with pytest.raises(ValueError, match="--wait requires"):
            scan_artifact(
                mock_client, component_id=_COMPONENT_ID, wait=True,
                repo=_REPO, path=None, poll_seconds=5, timeout_seconds=300,
            )


# ---------------------------------------------------------------------------
# no-wait path
# ---------------------------------------------------------------------------

def test_scan_artifact_no_wait_returns_immediately(mock_client: MagicMock) -> None:
    start_resp = {"info": "scan triggered"}
    with patch("xrayctl.api.scans.scan_artifact", return_value=start_resp):
        result = scan_artifact(
            mock_client, component_id=_COMPONENT_ID, wait=False,
            repo=None, path=None, poll_seconds=5, timeout_seconds=300,
        )
    assert result["ok"] is True
    assert result["component_id"] == _COMPONENT_ID
    assert result["started"] == start_resp


def test_scan_artifact_no_wait_does_not_poll(mock_client: MagicMock) -> None:
    with patch("xrayctl.api.scans.scan_artifact", return_value={}):
        with patch("xrayctl.api.scans.artifact_status") as mock_status:
            scan_artifact(
                mock_client, component_id=_COMPONENT_ID, wait=False,
                repo=None, path=None, poll_seconds=5, timeout_seconds=300,
            )
    mock_status.assert_not_called()


# ---------------------------------------------------------------------------
# wait / polling path
# ---------------------------------------------------------------------------

def test_scan_artifact_wait_polls_until_done(mock_client: MagicMock) -> None:
    with patch("xrayctl.api.scans.scan_artifact", return_value={"started": True}):
        with patch(
            "xrayctl.api.scans.artifact_status",
            return_value={"overall": {"status": "DONE"}},
        ):
            with patch("time.time", return_value=0):  # deadline never reached
                with patch("time.sleep"):
                    result = scan_artifact(
                        mock_client, component_id=_COMPONENT_ID, wait=True,
                        repo=_REPO, path=_PATH, poll_seconds=5, timeout_seconds=300,
                    )
    assert result["ok"] is True
    assert result["final_status"] == "DONE"


def test_scan_artifact_wait_stops_on_failed_status(mock_client: MagicMock) -> None:
    with patch("xrayctl.api.scans.scan_artifact", return_value={}):
        with patch(
            "xrayctl.api.scans.artifact_status",
            return_value={"overall": {"status": "FAILED"}},
        ):
            with patch("time.time", return_value=0):
                with patch("time.sleep"):
                    result = scan_artifact(
                        mock_client, component_id=_COMPONENT_ID, wait=True,
                        repo=_REPO, path=_PATH, poll_seconds=5, timeout_seconds=300,
                    )
    assert result["ok"] is False
    assert result["final_status"] == "FAILED"


def test_scan_artifact_wait_times_out(mock_client: MagicMock) -> None:
    # time.time() calls: [set deadline=5, enter loop at t=0, exit loop at t=400]
    with patch("xrayctl.api.scans.scan_artifact", return_value={}):
        with patch(
            "xrayctl.api.scans.artifact_status",
            return_value={"status": "SCANNING"},  # never terminal
        ):
            with patch("time.time", side_effect=[0, 0, 400]):
                with patch("time.sleep"):
                    result = scan_artifact(
                        mock_client, component_id=_COMPONENT_ID, wait=True,
                        repo=_REPO, path=_PATH, poll_seconds=1, timeout_seconds=5,
                    )
    assert result["ok"] is False
    assert "Timed out" in result["error"]


def test_scan_artifact_wait_result_includes_artifact_context(mock_client: MagicMock) -> None:
    with patch("xrayctl.api.scans.scan_artifact", return_value={}):
        with patch(
            "xrayctl.api.scans.artifact_status",
            return_value={"overall": {"status": "DONE"}},
        ):
            with patch("time.time", return_value=0):
                with patch("time.sleep"):
                    result = scan_artifact(
                        mock_client, component_id=_COMPONENT_ID, wait=True,
                        repo=_REPO, path=_PATH, poll_seconds=5, timeout_seconds=300,
                    )
    assert result["artifact"]["repo"] == _REPO
    assert result["artifact"]["path"] == _PATH
