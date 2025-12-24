from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from xrayctl.api.client import XrayClient
from xrayctl.api import repos as repos_api
from xrayctl.api import artifacts as artifacts_api


def _iter_all_repos(client: XrayClient, *, page_size: int) -> List[Dict[str, Any]]:
    offset = 0
    repos: List[Dict[str, Any]] = []

    while True:
        resp = repos_api.list_repos(client, offset=offset, num_of_rows=page_size)
        data = resp.get("data") or resp.get("repos") or []  # some envs differ in key name
        repos.extend(data)

        next_offset = resp.get("offset", -1)
        if next_offset == -1:
            break
        offset = int(next_offset)

    return repos


def _iter_all_artifacts_for_repo(client: XrayClient, *, repo: str, page_size: int) -> List[Dict[str, Any]]:
    offset = 0
    rows: List[Dict[str, Any]] = []

    while True:
        resp = artifacts_api.list_artifacts(client, repo=repo, offset=offset, num_of_rows=page_size)
        data = resp.get("data", [])
        rows.extend(data)

        next_offset = resp.get("offset", -1)
        if next_offset == -1:
            break
        offset = int(next_offset)

    return rows


def refresh_inventory(
    client: XrayClient,
    *,
    out_path: str,
    page_size: int,
    repo_page_size: int,
    repo_regex: Optional[str],
    include_repo_metadata: bool,
) -> Dict[str, Any]:
    if page_size < 1:
        raise ValueError("--page-size must be >= 1")
    if repo_page_size < 1:
        raise ValueError("--repo-page-size must be >= 1")

    repo_pat = re.compile(repo_regex) if repo_regex else None

    repos = _iter_all_repos(client, page_size=repo_page_size)

    # Normalize repo list to names + optional metadata
    repo_entries: List[Tuple[str, Dict[str, Any]]] = []
    for r in repos:
        # handle different shapes; most commonly the repo name field is `repo` or `name`
        name = r.get("repo") or r.get("name") or r.get("key")
        if not name:
            continue
        if repo_pat and not repo_pat.search(name):
            continue
        repo_entries.append((name, r))

    all_rows: List[Dict[str, Any]] = []

    for repo_name, repo_meta in repo_entries:
        artifacts = _iter_all_artifacts_for_repo(client, repo=repo_name, page_size=page_size)
        for a in artifacts:
            row = dict(a)
            row["repo"] = repo_name  # <-- the key requirement
            if include_repo_metadata:
                # Prefix repo metadata to avoid collisions
                for k, v in repo_meta.items():
                    if k in ("repo", "name", "key"):
                        continue
                    row[f"repo_{k}"] = v
            all_rows.append(row)

    df = pd.json_normalize(all_rows)

    # Persist
    if out_path.endswith(".parquet"):
        df.to_parquet(out_path, index=False)
    elif out_path.endswith(".csv"):
        df.to_csv(out_path, index=False)
    else:
        raise ValueError("--out must end with .parquet or .csv")

    return {
        "ok": True,
        "repos_total": len(repos),
        "repos_included": len(repo_entries),
        "artifacts_total": int(df.shape[0]),
        "out": out_path,
        "columns": list(df.columns),
    }
