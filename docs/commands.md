# xrayctl Commands

This document is the full reference for every command and flag in `xrayctl`.

All commands support:

- configuration via flags, environment variables, or config file (flags win)
- JSON or YAML output via `--format`
- structured error output and consistent exit codes

---

## Global flags

These flags work on every command.

| Flag | Env var | Description |
| --- | --- | --- |
| `--url` | `XRAY_URL` | JFrog platform base URL |
| `--token` | `XRAY_TOKEN` | JFrog access token |
| `--project` | `XRAY_PROJECT` | Xray project key (optional) |
| `--timeout` | `XRAY_TIMEOUT` | HTTP timeout in seconds (default: 30) |
| `--format` | `XRAY_FORMAT` | Output format: `json` (default) or `yaml` |
| `--config` | — | Path to config file (default: `~/.config/xrayctl/config.yaml`) |

---

## `xrayctl ping`

Verify connectivity and authentication against Xray.

```bash
xrayctl ping
```

**Example output:**

```json
{
  "ok": true,
  "response": { "status": "pong" }
}
```

---

## `xrayctl config`

Manage persistent CLI configuration stored at `~/.config/xrayctl/config.yaml`.

### `config init`

Create a default config file. Returns an error if the file already exists — use
`config set` to update individual values instead.

```bash
xrayctl config init
```

### `config set`

Set a single config value. Allowed keys: `url`, `token`, `project`, `timeout`, `format`.

```bash
xrayctl config set url https://jfrog.example.com
xrayctl config set token YOUR_TOKEN
xrayctl config set project MYPROJECT
xrayctl config set timeout 60
xrayctl config set format yaml
```

### `config save`

Save any flags passed on the command line into the config file. Only the flags
you explicitly provide are written — others are left unchanged.

```bash
xrayctl --url https://jfrog.example.com --project MYPROJECT config save
```

### `config view`

Show the effective configuration after merging flags, environment variables, and
the config file. The token is intentionally omitted from output.

```bash
xrayctl config view
```

**Example output:**

```json
{
  "ok": true,
  "effective": {
    "url": "https://jfrog.example.com",
    "project": null,
    "timeout": 30,
    "format": "json"
  }
}
```

---

## `xrayctl ignore-rules`

Manage Xray ignore rules.

### `ignore-rules create`

Create an ignore rule. At least one filter (`--cve`, `--vuln`, `--watch`, or
`--license`) is required. Use `--dry-run` to inspect the request body without
sending it.

```bash
xrayctl ignore-rules create \
  --note "temporary ignore pending fix" \
  --cve CVE-2024-1234 \
  --watch my-watch
```

| Flag | Description |
| --- | --- |
| `--note` | **(required)** Human-readable reason for the ignore rule |
| `--watch` | Watch name to scope the rule (repeatable) |
| `--cve` | CVE identifier, e.g. `CVE-2024-1234` (repeatable) |
| `--vuln` | Xray vulnerability ID (repeatable) |
| `--license` | License name or `any` (repeatable) |
| `--expires-at` | Expiration timestamp in ISO8601 UTC, e.g. `2026-01-01T00:00:00Z` |
| `--dry-run` | Print the request payload without creating the rule |

**Example — multiple filters:**

```bash
xrayctl ignore-rules create \
  --note "false positive on internal lib" \
  --cve CVE-2024-5678 \
  --watch prod-watch \
  --watch staging-watch \
  --expires-at 2026-06-01T00:00:00Z
```

**Example — dry run:**

```bash
xrayctl ignore-rules create --note "test" --cve CVE-2024-1234 --dry-run
```

```json
{
  "ok": true,
  "request": {
    "notes": "test",
    "ignore_filters": { "cves": ["CVE-2024-1234"] }
  }
}
```

---

### `ignore-rules list`

List ignore rules with optional filtering and pagination.

```bash
xrayctl ignore-rules list
xrayctl ignore-rules list --all
xrayctl ignore-rules list --cve CVE-2024-1234 --watch my-watch
```

| Flag | Description |
| --- | --- |
| `--watch` | Filter by watch name |
| `--policy` | Filter by policy name |
| `--vulnerability` | Filter by Xray vulnerability ID |
| `--cve` | Filter by CVE ID |
| `--license` | Filter by license name |
| `--component-name` | Filter by component name |
| `--component-version` | Filter by component version |
| `--expires-before` | ISO8601 UTC timestamp — rules expiring before this date |
| `--expires-after` | ISO8601 UTC timestamp — rules expiring after this date |
| `--page` | Page number, 1-based (default: 1) |
| `--rows` | Rows per page (default: 50) |
| `--order-by` | Field to sort by |
| `--direction` | Sort direction: `asc` or `desc` |
| `--all` | Fetch all pages automatically |

---

### `ignore-rules get`

Fetch a single ignore rule by ID.

```bash
xrayctl ignore-rules get <IGNORE_RULE_ID>
```

---

## `xrayctl scan artifact`

Trigger an on-demand scan for a specific artifact. By default the command returns
immediately after triggering. Use `--wait` to poll until the scan reaches a
terminal state.

```bash
# Trigger and return immediately
xrayctl scan artifact --component-id docker://alpine:3.20

# Trigger and wait for completion
xrayctl scan artifact \
  --component-id docker://alpine:3.20 \
  --repo my-docker-repo \
  --path alpine/3.20 \
  --wait
```

| Flag | Description |
| --- | --- |
| `--component-id` | **(required)** Xray component identifier, e.g. `docker://alpine:3.20` |
| `--wait` | Poll until scan reaches a terminal status (`DONE`, `FAILED`, `PARTIAL`, `NOT_SUPPORTED`) |
| `--repo` | Repository key — required when `--wait` is set |
| `--path` | Artifact path in repo — required when `--wait` is set |
| `--poll-seconds` | Polling interval in seconds (default: 5) |
| `--timeout-seconds` | Maximum wait time in seconds (default: 300) |

**Terminal statuses:**

| Status | `ok` | Meaning |
| --- | --- | --- |
| `DONE` | `true` | Scan completed successfully |
| `FAILED` | `false` | Scan failed |
| `PARTIAL` | `false` | Scan partially completed |
| `NOT_SUPPORTED` | `false` | Artifact type not supported |

---

## `xrayctl artifacts refresh`

Fetch all artifacts across every repository known to Xray and write them to a
local file for offline analysis. See [artifacts.md](artifacts.md) for details.

```bash
xrayctl artifacts refresh --out artifacts.parquet
```

| Flag | Description |
| --- | --- |
| `--out` | Output file path — must end in `.parquet` or `.csv` (default: `artifacts.parquet`) |
| `--page-size` | Artifacts per page per request (default: 200) |
| `--repo-page-size` | Repositories per page per request (default: 200) |
| `--repo-regex` | Only include repositories whose name matches this regex |
| `--include-repo-metadata` | Add repo metadata columns (prefixed `repo_`) to each row |

**Example output:**

```json
{
  "ok": true,
  "repos_total": 42,
  "repos_included": 12,
  "artifacts_total": 3847,
  "out": "artifacts.parquet",
  "columns": ["repo", "name", "repo_path", "sha256", "created", "size"]
}
```
