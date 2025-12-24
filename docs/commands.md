# xrayctl Commands

This document describes the user-facing commands provided by `xrayctl`.

All commands support:

- configuration via flags, environment variables, or config file
- JSON or YAML output (`--format`)
- consistent error handling

---

## `xrayctl ping`

Verify connectivity and authentication against Xray.

```bash
xrayctl ping
```

---

## `xrayctl config`

Manage persistent CLI configuration.

### Initialize config

```bash
xrayctl config init
```

### Set a value

```bash
xrayctl config set url https://jfrog.example.com
xrayctl config set project MYPROJECT
```

### Save flags to config

```bash
xrayctl --url https://jfrog.example.com --project MYPROJECT config save
```

### View effective config

```bash
xrayctl config view
```

---

## `xrayctl ignore-rules`

Manage Xray ignore rules.

### Create

```bash
xrayctl ignore-rules create --note "temporary ignore" --cve CVE-2024-1234
```

### List

```bash
xrayctl ignore-rules list --all
```

### Get by ID

```bash
xrayctl ignore-rules get <IGNORE_RULE_ID>
```

---

## `xrayctl scan artifact`

Trigger an on-demand scan for an artifact.

```bash
xrayctl scan artifact --component-id docker://alpine:3.20
```

---

## `xrayctl artifacts refresh`

Fetch all artifacts across all repositories and store them locally.

```bash
xrayctl artifacts refresh --out artifacts.parquet
```
