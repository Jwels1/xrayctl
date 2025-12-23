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

    return p
