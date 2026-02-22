# Artifact Inventory

This document describes the artifact inventory feature of `xrayctl`.

The artifact inventory is a **local, persistent cache** of artifacts fetched from
Xray, designed for offline analysis and higher-level automation.

---

## What the inventory is

The inventory is a flat table where:

- each row represents a single artifact
- artifacts are fetched across **all repositories** (or a filtered subset)
- a `repo` column explicitly identifies the origin repository

The inventory is stored as:

- **Parquet** (recommended — compact, typed, fast to query with pandas)
- **CSV** (plain text, compatible with anything)

---

## How inventory data is collected

The refresh process:

1. Lists all repositories known to Xray (paginated)
2. Optionally filters repositories by name using `--repo-regex`
3. For each included repository, lists all artifacts (paginated)
4. Normalizes all artifacts into a flat table using `pandas.json_normalize`
5. Injects a `repo` column on every row
6. Optionally adds repo metadata columns (prefixed `repo_`) when `--include-repo-metadata` is set
7. Writes the result to disk

---

## Running a refresh

```bash
# Basic refresh — writes to artifacts.parquet
xrayctl artifacts refresh

# Custom output path
xrayctl artifacts refresh --out ~/data/artifacts.parquet

# CSV instead of Parquet
xrayctl artifacts refresh --out artifacts.csv

# Only include prod repositories
xrayctl artifacts refresh --repo-regex "^prod-"

# Include repo metadata columns
xrayctl artifacts refresh --include-repo-metadata

# Tune page sizes for large or slow instances
xrayctl artifacts refresh --page-size 100 --repo-page-size 50
```

---

## Flags

| Flag | Default | Description |
| --- | --- | --- |
| `--out` | `artifacts.parquet` | Output file path (`.parquet` or `.csv`) |
| `--page-size` | `200` | Artifacts per request per repo |
| `--repo-page-size` | `200` | Repositories per request |
| `--repo-regex` | — | Only include repos whose name matches this regex |
| `--include-repo-metadata` | off | Add `repo_*` columns from the repo metadata to each row |

---

## Typical columns

Column names depend on your Xray version and repository types. Common ones:

| Column | Description |
| --- | --- |
| `repo` | Repository name (always present — injected by xrayctl) |
| `name` | Artifact filename |
| `repo_path` | Path inside the repository |
| `repo_full_path` | Full path including the repository name |
| `sha256` | SHA-256 checksum |
| `created` | Creation timestamp |
| `size` | Artifact size in bytes |

When `--include-repo-metadata` is used, additional `repo_*` columns are added
from each repository's metadata (e.g. `repo_type`, `repo_package_type`).

---

## Querying the inventory with pandas

```python
import pandas as pd

df = pd.read_parquet("artifacts.parquet")

# Filter by repo
df[df["repo"] == "prod-docker"]

# Find artifacts by name pattern
df[df["name"].str.contains(r"^alpine", regex=True, na=False)]

# Find large artifacts (> 100 MB)
df[df["size"] > 100 * 1024 * 1024]

# Count artifacts per repo
df.groupby("repo").size().sort_values(ascending=False)

# Find artifacts created in the last 30 days
df["created"] = pd.to_datetime(df["created"])
df[df["created"] > pd.Timestamp.now() - pd.Timedelta(days=30)]
```

---

## Pagination and large instances

The refresh auto-paginates both the repository list and the artifact list using
the offset returned by the Xray API. It stops when:

- the API signals the last page (offset `-1`)
- the page returns no data
- the offset does not advance (guard against API edge cases)

For very large instances, tune `--page-size` and `--repo-page-size` downward if
you experience timeouts, or increase `--timeout` globally.
