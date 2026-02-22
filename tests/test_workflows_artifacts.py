from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pandas as pd
import pytest

from xrayctl.api.client import XrayClient
from xrayctl.workflows.artifacts import (
    _iter_all_artifacts_for_repo,
    _iter_all_repos,
    refresh_inventory,
)


@pytest.fixture
def mock_client() -> MagicMock:
    c = MagicMock(spec=XrayClient)
    c.project = None
    return c


# ---------------------------------------------------------------------------
# _iter_all_repos
# ---------------------------------------------------------------------------

def test_iter_all_repos_single_page(mock_client: MagicMock) -> None:
    page = {"data": [{"repo": "repo-a"}, {"repo": "repo-b"}], "offset": -1}
    with patch("xrayctl.api.repos.list_repos", return_value=page):
        result = _iter_all_repos(mock_client, page_size=200)
    assert len(result) == 2
    assert result[0]["repo"] == "repo-a"


def test_iter_all_repos_multiple_pages(mock_client: MagicMock) -> None:
    pages = [
        {"data": [{"repo": "repo-a"}, {"repo": "repo-b"}], "offset": 200},
        {"data": [{"repo": "repo-c"}], "offset": -1},
    ]
    with patch("xrayctl.api.repos.list_repos", side_effect=pages):
        result = _iter_all_repos(mock_client, page_size=200)
    assert len(result) == 3


def test_iter_all_repos_stops_on_empty_data(mock_client: MagicMock) -> None:
    pages = [
        {"data": [{"repo": "repo-a"}], "offset": 200},
        {"data": [], "offset": 400},
    ]
    with patch("xrayctl.api.repos.list_repos", side_effect=pages):
        result = _iter_all_repos(mock_client, page_size=200)
    assert len(result) == 1


def test_iter_all_repos_stops_when_offset_unchanged(mock_client: MagicMock) -> None:
    # offset stays at 0 — infinite loop guard
    pages = [{"data": [{"repo": "repo-a"}], "offset": 0}]
    with patch("xrayctl.api.repos.list_repos", side_effect=pages):
        result = _iter_all_repos(mock_client, page_size=200)
    assert len(result) == 1


# ---------------------------------------------------------------------------
# _iter_all_artifacts_for_repo
# ---------------------------------------------------------------------------

def test_iter_all_artifacts_single_page(mock_client: MagicMock) -> None:
    page = {"data": [{"name": "a.jar"}, {"name": "b.jar"}], "offset": -1}
    with patch("xrayctl.api.artifacts.list_artifacts", return_value=page):
        result = _iter_all_artifacts_for_repo(mock_client, repo="my-repo", page_size=200)
    assert len(result) == 2


def test_iter_all_artifacts_multiple_pages(mock_client: MagicMock) -> None:
    pages = [
        {"data": [{"name": "a.jar"}], "offset": 200},
        {"data": [{"name": "b.jar"}], "offset": -1},
    ]
    with patch("xrayctl.api.artifacts.list_artifacts", side_effect=pages):
        result = _iter_all_artifacts_for_repo(mock_client, repo="my-repo", page_size=200)
    assert len(result) == 2


def test_iter_all_artifacts_stops_on_empty_data(mock_client: MagicMock) -> None:
    pages = [
        {"data": [{"name": "a.jar"}], "offset": 200},
        {"data": [], "offset": 400},
    ]
    with patch("xrayctl.api.artifacts.list_artifacts", side_effect=pages):
        result = _iter_all_artifacts_for_repo(mock_client, repo="my-repo", page_size=200)
    assert len(result) == 1


def test_iter_all_artifacts_stops_when_offset_unchanged(mock_client: MagicMock) -> None:
    pages = [{"data": [{"name": "a.jar"}], "offset": 0}]
    with patch("xrayctl.api.artifacts.list_artifacts", side_effect=pages):
        result = _iter_all_artifacts_for_repo(mock_client, repo="my-repo", page_size=200)
    assert len(result) == 1


# ---------------------------------------------------------------------------
# refresh_inventory
# ---------------------------------------------------------------------------

def test_refresh_inventory_raises_when_page_size_below_1(
    tmp_path: Path, mock_client: MagicMock
) -> None:
    with pytest.raises(ValueError, match="--page-size"):
        refresh_inventory(
            mock_client, out_path=str(tmp_path / "out.parquet"),
            page_size=0, repo_page_size=200, repo_regex=None, include_repo_metadata=False,
        )


def test_refresh_inventory_raises_when_repo_page_size_below_1(
    tmp_path: Path, mock_client: MagicMock
) -> None:
    with pytest.raises(ValueError, match="--repo-page-size"):
        refresh_inventory(
            mock_client, out_path=str(tmp_path / "out.parquet"),
            page_size=200, repo_page_size=0, repo_regex=None, include_repo_metadata=False,
        )


def test_refresh_inventory_raises_on_unknown_extension(
    tmp_path: Path, mock_client: MagicMock
) -> None:
    repo_page = {"data": [{"repo": "my-repo"}], "offset": -1}
    art_page: dict = {"data": [], "offset": -1}
    with patch("xrayctl.api.repos.list_repos", return_value=repo_page):
        with patch("xrayctl.api.artifacts.list_artifacts", return_value=art_page):
            with pytest.raises(ValueError, match=".parquet or .csv"):
                refresh_inventory(
                    mock_client, out_path=str(tmp_path / "out.json"),
                    page_size=200, repo_page_size=200,
                    repo_regex=None, include_repo_metadata=False,
                )


def test_refresh_inventory_writes_parquet(tmp_path: Path, mock_client: MagicMock) -> None:
    out_path = str(tmp_path / "artifacts.parquet")
    repo_page = {"data": [{"repo": "my-repo"}], "offset": -1}
    art_page = {"data": [{"name": "lib.jar", "sha256": "abc123"}], "offset": -1}
    with patch("xrayctl.api.repos.list_repos", return_value=repo_page):
        with patch("xrayctl.api.artifacts.list_artifacts", return_value=art_page):
            result = refresh_inventory(
                mock_client, out_path=out_path,
                page_size=200, repo_page_size=200,
                repo_regex=None, include_repo_metadata=False,
            )
    assert result["ok"] is True
    assert Path(out_path).exists()
    df = pd.read_parquet(out_path)
    assert len(df) == 1
    assert "repo" in df.columns


def test_refresh_inventory_writes_csv(tmp_path: Path, mock_client: MagicMock) -> None:
    out_path = str(tmp_path / "artifacts.csv")
    repo_page = {"data": [{"repo": "my-repo"}], "offset": -1}
    art_page = {"data": [{"name": "lib.jar"}], "offset": -1}
    with patch("xrayctl.api.repos.list_repos", return_value=repo_page):
        with patch("xrayctl.api.artifacts.list_artifacts", return_value=art_page):
            result = refresh_inventory(
                mock_client, out_path=out_path,
                page_size=200, repo_page_size=200,
                repo_regex=None, include_repo_metadata=False,
            )
    assert result["ok"] is True
    assert Path(out_path).exists()


def test_refresh_inventory_applies_repo_regex(tmp_path: Path, mock_client: MagicMock) -> None:
    out_path = str(tmp_path / "artifacts.parquet")
    repo_page = {
        "data": [{"repo": "match-prod"}, {"repo": "skip-dev"}],
        "offset": -1,
    }
    art_page = {"data": [{"name": "lib.jar"}], "offset": -1}
    with patch("xrayctl.api.repos.list_repos", return_value=repo_page):
        with patch("xrayctl.api.artifacts.list_artifacts", return_value=art_page) as mock_arts:
            result = refresh_inventory(
                mock_client, out_path=out_path,
                page_size=200, repo_page_size=200,
                repo_regex="^match-", include_repo_metadata=False,
            )
    assert result["repos_total"] == 2
    assert result["repos_included"] == 1
    assert mock_arts.call_count == 1


def test_refresh_inventory_returns_correct_summary(tmp_path: Path, mock_client: MagicMock) -> None:
    out_path = str(tmp_path / "artifacts.parquet")
    repo_page = {
        "data": [{"repo": "repo-a"}, {"repo": "repo-b"}],
        "offset": -1,
    }

    def list_arts_side_effect(*args: object, **kwargs: object) -> dict:
        return {"data": [{"name": "artifact.jar"}], "offset": -1}

    with patch("xrayctl.api.repos.list_repos", return_value=repo_page):
        with patch("xrayctl.api.artifacts.list_artifacts", side_effect=list_arts_side_effect):
            result = refresh_inventory(
                mock_client, out_path=out_path,
                page_size=200, repo_page_size=200,
                repo_regex=None, include_repo_metadata=False,
            )
    assert result["repos_total"] == 2
    assert result["repos_included"] == 2
    assert result["artifacts_total"] == 2
    assert result["out"] == out_path


def test_refresh_inventory_adds_repo_column(tmp_path: Path, mock_client: MagicMock) -> None:
    out_path = str(tmp_path / "artifacts.parquet")
    repo_page = {"data": [{"repo": "my-repo"}], "offset": -1}
    art_page = {"data": [{"name": "lib.jar"}], "offset": -1}
    with patch("xrayctl.api.repos.list_repos", return_value=repo_page):
        with patch("xrayctl.api.artifacts.list_artifacts", return_value=art_page):
            refresh_inventory(
                mock_client, out_path=out_path,
                page_size=200, repo_page_size=200,
                repo_regex=None, include_repo_metadata=False,
            )
    df = pd.read_parquet(out_path)
    assert df["repo"].iloc[0] == "my-repo"
