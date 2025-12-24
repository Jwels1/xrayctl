# xrayctl Architecture

This document describes the internal architecture of `xrayctl` and how requests,
data, and control flow through the system.

The design prioritizes:

- clarity over cleverness
- separation of concerns
- long-term maintainability

---

## High-level overview

`xrayctl` is structured into four layers:

CLI (argparse)
   ↓
main.py (orchestration)
   ↓
workflows/ (business logic)
   ↓
api/ (Xray REST wrappers)
   ↓
JFrog Xray

Each layer has a single, clearly defined responsibility.

---

## CLI Parsing (`xrayparser.py`)

The CLI layer defines the *grammar* of the tool:

- commands
- subcommands
- flags
- help text

It does **not**:

- perform validation
- make API calls
- implement business logic

Each command path sets a `handler` via `set_defaults(handler=...)`, which is later
used by `main.py` to dispatch to the correct workflow.

---

## Orchestration (`main.py`)

`main.py` is the control plane of the CLI.

Responsibilities:

- parse arguments
- load configuration (flags → env → config file)
- initialize `XrayClient`
- dispatch to the correct workflow based on `args.handler`
- enforce consistent error handling and exit codes

---

## Workflow Layer (`workflows/`)

Workflows implement **user-facing operations**.

Responsibilities:

- validate inputs
- normalize and enrich data
- orchestrate one or more API calls
- return structured, CLI-friendly results

Workflows are intentionally:

- testable in isolation
- independent of CLI parsing
- free of HTTP details

---

## API Layer (`api/`)

The API layer contains **thin wrappers** around Xray REST endpoints.

Design rules:

- one function per endpoint
- minimal transformation
- no business logic
- no CLI concerns

---

## Error handling model

Errors are handled centrally in `main.py`.

- HTTP errors from Xray → exit code `2`
- validation or configuration errors → exit code `1`
- success → exit code `0`

All errors are printed in structured JSON or YAML.
