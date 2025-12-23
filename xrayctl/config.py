from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "xrayctl" / "config.yaml"

@dataclass
class Settings:
    url: Optional[str] = None
    token: Optional[str] = None
    project: Optional[str] = None
    timeout: int = 30
    fmt: str = "json"

def _read_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def load_settings(url, token, project, timeout, fmt, config_path) -> Settings:
    path = Path(config_path).expanduser() if config_path else DEFAULT_CONFIG_PATH
    cfg = _read_yaml(path)

    return Settings(
        url=url or os.getenv("XRAY_URL") or cfg.get("url"),
        token=token or os.getenv("XRAY_TOKEN") or cfg.get("token"),
        project=project or os.getenv("XRAY_PROJECT") or cfg.get("project"),
        timeout=int(timeout or os.getenv("XRAY_TIMEOUT") or cfg.get("timeout", 30)),
        fmt=fmt or os.getenv("XRAY_FORMAT") or cfg.get("format", "json"),
    )

def default_config() -> Dict[str, Any]:
    return {
        "url": None,
        "token": None,
        "project": None,
        "timeout": 30,
        "format": "json",
    }

def _resolve_config_path(config_path: Optional[str]) -> Path:
    return Path(config_path).expanduser() if config_path else DEFAULT_CONFIG_PATH

def write_config(data: Dict[str, Any], config_path: Optional[str] = None) -> Path:
    path = _resolve_config_path(config_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)

    # Best-effort: restrict permissions if token present (Unix-y systems)
    if "token" in data and data.get("token"):
        try:
            os.chmod(path, 0o600)
        except Exception:
            pass

    return path

def update_config(patch: Dict[str, Any], config_path: Optional[str] = None) -> Path:
    path = _resolve_config_path(config_path)
    current = _read_yaml(path)
    # only apply keys that are not None
    for k, v in patch.items():
        if v is not None:
            current[k] = v
    return write_config(current, config_path=str(path))
