# xrayctl

`xrayctl` is a custom CLI for JFrog Xray focused on **automation, artifact inventory,
and policy-oriented workflows**.

Unlike the official JFrog CLI, `xrayctl` is designed to:

- expose Xray concepts in a scriptable, composable way
- support inventory-style workflows (DataFrame-backed)
- make it easy to build higher-level logic (regex rules, bulk operations)

## Features

- Xray connectivity check (`ping`)
- Ignore rule management
  - create
  - list
  - get by ID
- Artifact scanning (on-demand, artifact-only)
- Artifact inventory refresh across **all repositories**
- Local artifact cache (Parquet / CSV) for offline analysis
- Explicit config management (`xrayctl config …`)

## Installation

### Development install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .


# Initialize config
xrayctl config init

# Set Xray URL
xrayctl config set url https://jfrog.example.com

# Set token (or export XRAY_TOKEN env var)
xrayctl config set token YOUR_TOKEN

# Verify connectivity
xrayctl ping
