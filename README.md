# xrayctl

`xrayctl` is a custom CLI for JFrog Xray focused on **automation, artifact inventory,
and policy-oriented workflows**.

Unlike the official JFrog CLI, `xrayctl` is designed to:

- expose Xray concepts in a scriptable, composable way
- support inventory-style workflows (DataFrame-backed)
- make it easy to build higher-level logic (regex rules, bulk operations)

## Features

- Xray connectivity check (`ping`)
- Ignore rule management — create, list (with full filtering + auto-pagination), get by ID
- Artifact scanning — on-demand trigger with optional `--wait` polling
- Artifact inventory refresh across **all repositories** with optional repo regex filter
- Local artifact cache (Parquet / CSV) for offline analysis
- Explicit config management (`xrayctl config …`)

## Installation

### Development install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### First-time setup

```bash
# Create a default config file
xrayctl config init

# Set your Xray URL
xrayctl config set url https://jfrog.example.com

# Set your token (or use the XRAY_TOKEN env var instead)
xrayctl config set token YOUR_TOKEN

# Verify connectivity
xrayctl ping
```

## Configuration

Settings are resolved in this priority order (highest wins):

| Source | Example |
| --- | --- |
| CLI flag | `--url https://jfrog.example.com` |
| Environment variable | `XRAY_URL`, `XRAY_TOKEN`, `XRAY_PROJECT`, `XRAY_TIMEOUT`, `XRAY_FORMAT` |
| Config file | `~/.config/xrayctl/config.yaml` |

## Output

All commands output JSON by default. Pass `--format yaml` for YAML.

```bash
xrayctl ping --format yaml
xrayctl ignore-rules list --all --format yaml
```

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Success |
| `1` | Validation or configuration error |
| `2` | Xray API HTTP error |

## Running tests

```bash
pip install -e ".[test]"
pytest
pytest -v        # verbose
pytest -x        # stop on first failure
```

## Quick examples

```bash
# List all ignore rules
xrayctl ignore-rules list --all

# Create an ignore rule (dry-run first)
xrayctl ignore-rules create --note "assess later" --cve CVE-2024-1234 --watch my-watch --dry-run

# Trigger a scan and wait for it to finish
xrayctl scan artifact \
  --component-id docker://alpine:3.20 \
  --repo my-docker-repo \
  --path alpine/3.20 \
  --wait

# Refresh artifact inventory for prod repos only
xrayctl artifacts refresh --out artifacts.parquet --repo-regex "^prod-"
```

For full command reference see [docs/commands.md](docs/commands.md).
