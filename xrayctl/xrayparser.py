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


    ir_list = ir_sub.add_parser("list", help="List ignore rules")
    # Common filters (start small; you can add more later)
    ir_list.add_argument("--watch", help="Filter by watch name")
    ir_list.add_argument("--policy", help="Filter by policy name")
    ir_list.add_argument("--vulnerability", help="Filter by vulnerability id")
    ir_list.add_argument("--cve", help="Filter by CVE id")
    ir_list.add_argument("--license", help="Filter by license name")
    ir_list.add_argument("--component-name", help="Filter by component name")
    ir_list.add_argument("--component-version", help="Filter by component version")

    # Pagination/sorting (Xray supports these) :contentReference[oaicite:1]{index=1}
    ir_list.add_argument("--page", type=int, default=1, help="Page number (page_num)")
    ir_list.add_argument("--rows", type=int, default=50, help="Rows per page (num_of_rows)")
    ir_list.add_argument("--order-by", default=None, help="Order by field (order_by)")
    ir_list.add_argument("--direction", choices=["asc", "desc"], default=None, help="Sort direction")

    # Expiration filtering :contentReference[oaicite:2]{index=2}
    ir_list.add_argument("--expires-before", default=None, help="ISO8601 UTC timestamp")
    ir_list.add_argument("--expires-after", default=None, help="ISO8601 UTC timestamp")

    # Convenience: fetch all pages
    ir_list.add_argument("--all", action="store_true", help="Fetch all pages")

    ir_list.set_defaults(handler="ignore_rules_list")

    ir_get = ir_sub.add_parser("get", help="Get a single ignore rule by ID")
    ir_get.add_argument("id", help="Ignore rule id")
    ir_get.set_defaults(handler="ignore_rules_get")



    # scan
    scan = sub.add_parser("scan", help="Trigger Xray scans")
    scan_sub = scan.add_subparsers(dest="subcommand", required=True)

    scan_art = scan_sub.add_parser("artifact", help="Trigger an on-demand scan for an artifact")
    scan_art.add_argument(
        "--component-id",
        required=True,
        help="Component identifier (Xray componentID), e.g. docker://alpine:3.20",
    )

    # Optional: enable waiting/polling if repo+path provided (artifact status API uses these)
    scan_art.add_argument("--repo", default=None, help="Repo key for status polling (required for --wait)")
    scan_art.add_argument("--path", default=None, help="Artifact path in repo for status polling (required for --wait)")
    scan_art.add_argument("--wait", action="store_true", help="Poll status until scan completes (requires --repo and --path)")
    scan_art.add_argument("--poll-seconds", type=int, default=5, help="Polling interval when --wait is set")
    scan_art.add_argument("--timeout-seconds", type=int, default=300, help="Max wait time when --wait is set")

    scan_art.set_defaults(handler="scan_artifact")


    # artifacts
    arts = sub.add_parser("artifacts", help="Artifact inventory commands")
    arts_sub = arts.add_subparsers(dest="subcommand", required=True)

    arts_refresh = arts_sub.add_parser("refresh", help="Fetch all artifacts across all repos and write to disk")
    arts_refresh.add_argument("--out", default="artifacts.parquet", help="Output file (.parquet or .csv)")
    arts_refresh.add_argument("--page-size", type=int, default=200, help="Artifacts page size per request")
    arts_refresh.add_argument("--repo-page-size", type=int, default=200, help="Repos page size per request")
    arts_refresh.add_argument("--repo-regex", default=None, help="Only include repos whose name matches this regex")
    arts_refresh.add_argument("--include-repo-metadata", action="store_true", help="Add repo metadata columns if available")
    arts_refresh.set_defaults(handler="artifacts_refresh")


    return p
