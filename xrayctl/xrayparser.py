import argparse

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="xrayctl")

    # Global flags
    p.add_argument("--config", default=None, help="Path to config yaml (default: ~/.config/xrayctl/config.yaml)")
    p.add_argument("--url", default=None, help="JFrog platform base URL (e.g. https://jfrog.example.com)")
    p.add_argument("--token", default=None, help="JFrog access token")
    p.add_argument("--project", default=None, help="Optional Xray project key")
    p.add_argument("--timeout", type=int, default=None, help="HTTP timeout seconds")
    p.add_argument("--format", choices=["json", "yaml"], default=None, help="Output format")

    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("hello", help="Sanity check the CLI wiring")

    ping = sub.add_parser("ping", help="Check connectivity/auth against Xray")
    ping.set_defaults(handler="ping")

    # --- NEW: config commands ---
    cfg = sub.add_parser("config", help="Manage xrayctl configuration")
    cfg_sub = cfg.add_subparsers(dest="subcommand", required=True)

    cfg_init = cfg_sub.add_parser("init", help="Create a default config file if missing")
    cfg_init.set_defaults(handler="config_init")

    cfg_view = cfg_sub.add_parser("view", help="Show the effective configuration (merged)")
    cfg_view.set_defaults(handler="config_view")

    cfg_set = cfg_sub.add_parser("set", help="Set a config value")
    cfg_set.add_argument("key", choices=["url", "token", "project", "timeout", "format"])
    cfg_set.add_argument("value")
    cfg_set.set_defaults(handler="config_set")

    cfg_save = cfg_sub.add_parser("save", help="Save provided flags into the config file (only fields you passed)")
    cfg_save.set_defaults(handler="config_save")


    # ignore-rules
    ir = sub.add_parser("ignore-rules", help="Ignore rules operations")
    ir_sub = ir.add_subparsers(dest="subcommand", required=True)

    ir_create = ir_sub.add_parser("create", help="Create an ignore rule")
    ir_create.add_argument("--note", required=True, help="Notes for the ignore rule")

    # filters (repeatable)
    ir_create.add_argument("--watch", action="append", default=[], help="Watch name (repeatable)")
    ir_create.add_argument("--cve", action="append", default=[], help="CVE id (repeatable), e.g. CVE-2024-1234")
    ir_create.add_argument("--vuln", action="append", default=[], help="Xray vulnerability id (repeatable)")
    ir_create.add_argument("--license", action="append", default=[], help="License name or 'any' (repeatable)")

    # optional scope-like filters you’ll likely want soon (start minimal)
    # ir_create.add_argument("--repo", action="append", default=[], help="Repo key (repeatable)")

    ir_create.add_argument("--expires-at", default=None, help="ISO8601 UTC timestamp, e.g. 2026-01-01T00:00:00Z")
    ir_create.add_argument("--dry-run", action="store_true", help="Print the ignore rule body without creating")
    ir_create.set_defaults(handler="ignore_rules_create")

    return p
