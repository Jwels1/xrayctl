# Artifact Inventory

This document describes the artifact inventory feature of `xrayctl`.

The artifact inventory is a **local, persistent cache** of artifacts fetched from
Xray, designed for offline analysis and higher-level automation.

---

## What the inventory is

The inventory is a flat table where:

- each row represents a single artifact
- artifacts are fetched across **all repositories**
- a `repo` column explicitly identifies origin

The inventory is stored as:

- Parquet (recommended)
- or CSV

---

## How inventory data is collected

The refresh process performs:

1. List all repositories known to Xray
2. For each repository:
   - list artifacts using the Xray inventory API
   - page through results using offsets
3. Normalize artifacts into rows
4. Inject `repo` explicitly
5. Persist the result to disk

---

## What data is included

Typical columns include (varies by repo type):

| Column | Description |
| ------ | ------------ |
| repo | Repository name |
| name | Artifact name |
| repo_path | Path inside the repo |
| repo_full_path | Full path including repo |
| created | Creation timestamp |
| size | Artifact size |

---

## Example usage

Refresh inventory:

```bash
xrayctl artifacts refresh --out artifacts.parquet
```

Load and query:

```python
import pandas as pd

df = pd.read_parquet("artifacts.parquet")
df[df["name"].str.contains(r"^alpine", regex=True, na=False)]
```
