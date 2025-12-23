from __future__ import annotations

from typing import Any, Dict, Optional

from xrayctl.config import default_config, load_settings, update_config, write_config

_ALLOWED_KEYS = {"url", "token", "project", "timeout", "format"}


def init_config(config_path: Optional[str]) -> Dict[str, Any]:
    # Create default config (overwrites if already exists; you can change to "only if missing" later)
    path = write_config(default_config(), config_path=config_path)
    return {"ok": True, "path": str(path)}


def set_value(config_path: Optional[str], key: str, value: str) -> Dict[str, Any]:
    if key not in _ALLOWED_KEYS:
        raise ValueError(f"Unsupported key: {key}")

    # basic coercion
    if key == "timeout":
        value = int(value)

    path = update_config({key: value}, config_path=config_path)
    return {"ok": True, "path": str(path), "updated": {key: value}}


def save_from_flags(args) -> Dict[str, Any]:
    # Save only what was explicitly provided via flags
    patch: Dict[str, Any] = {}
    if args.url is not None:
        patch["url"] = args.url
    if args.token is not None:
        patch["token"] = args.token
    if args.project is not None:
        patch["project"] = args.project
    if args.timeout is not None:
        patch["timeout"] = args.timeout
    if args.format is not None:
        patch["format"] = args.format

    if not patch:
        raise ValueError("No flags provided to save. Provide --url/--token/--project/--timeout/--format.")

    path = update_config(patch, config_path=args.config)
    # don’t echo token back
    redacted = dict(patch)
    if "token" in redacted:
        redacted["token"] = "***"
    return {"ok": True, "path": str(path), "saved": redacted}


def view_effective(args) -> Dict[str, Any]:
    s = load_settings(
        url=args.url,
        token=args.token,
        project=args.project,
        timeout=args.timeout,
        fmt=args.format,
        config_path=args.config,
    )
    # Don’t print token by default
    return {
        "ok": True,
        "effective": {
            "url": s.url,
            "project": s.project,
            "timeout": s.timeout,
            "format": s.fmt,
        },
    }
