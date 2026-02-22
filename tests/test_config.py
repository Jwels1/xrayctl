from __future__ import annotations

import stat
from pathlib import Path

import pytest
import yaml

from xrayctl.config import (
    default_config,
    load_settings,
    update_config,
    write_config,
)


def test_default_config_structure() -> None:
    cfg = default_config()
    assert set(cfg.keys()) == {"url", "token", "project", "timeout", "format"}
    assert cfg["timeout"] == 30
    assert cfg["format"] == "json"
    assert cfg["url"] is None
    assert cfg["token"] is None


# --- load_settings ---

def test_load_settings_from_flags() -> None:
    s = load_settings(
        url="https://flag.example.com",
        token="flag-token",
        project="flag-proj",
        timeout=60,
        fmt="yaml",
        config_path=None,
    )
    assert s.url == "https://flag.example.com"
    assert s.token == "flag-token"
    assert s.project == "flag-proj"
    assert s.timeout == 60
    assert s.fmt == "yaml"


def test_load_settings_flags_win_over_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XRAY_URL", "https://env.example.com")
    monkeypatch.setenv("XRAY_TOKEN", "env-token")
    s = load_settings(
        url="https://flag.example.com",
        token="flag-token",
        project=None,
        timeout=None,
        fmt=None,
        config_path=None,
    )
    assert s.url == "https://flag.example.com"
    assert s.token == "flag-token"


def test_load_settings_env_wins_over_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("url: https://file.example.com\ntoken: file-token\n")
    monkeypatch.setenv("XRAY_URL", "https://env.example.com")
    monkeypatch.setenv("XRAY_TOKEN", "env-token")
    s = load_settings(
        url=None, token=None, project=None, timeout=None, fmt=None,
        config_path=str(cfg_file),
    )
    assert s.url == "https://env.example.com"
    assert s.token == "env-token"


def test_load_settings_from_file(tmp_path: Path) -> None:
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(
        "url: https://file.example.com\ntoken: file-token\ntimeout: 15\nformat: yaml\n"
    )
    s = load_settings(
        url=None, token=None, project=None, timeout=None, fmt=None,
        config_path=str(cfg_file),
    )
    assert s.url == "https://file.example.com"
    assert s.token == "file-token"
    assert s.timeout == 15
    assert s.fmt == "yaml"


def test_load_settings_defaults_when_nothing_configured(tmp_path: Path) -> None:
    s = load_settings(
        url=None, token=None, project=None, timeout=None, fmt=None,
        config_path=str(tmp_path / "missing.yaml"),
    )
    assert s.url is None
    assert s.token is None
    assert s.timeout == 30
    assert s.fmt == "json"


# --- write_config ---

def test_write_config_creates_file_and_parents(tmp_path: Path) -> None:
    cfg_file = tmp_path / "sub" / "config.yaml"
    path = write_config({"url": "https://a.com", "token": None}, config_path=str(cfg_file))
    assert path.exists()
    data = yaml.safe_load(path.read_text())
    assert data["url"] == "https://a.com"


def test_write_config_sets_600_when_token_present(tmp_path: Path) -> None:
    cfg_file = tmp_path / "config.yaml"
    write_config({"token": "my-secret"}, config_path=str(cfg_file))
    assert stat.S_IMODE(cfg_file.stat().st_mode) == 0o600


def test_write_config_no_permission_change_without_token(tmp_path: Path) -> None:
    cfg_file = tmp_path / "config.yaml"
    write_config({"url": "https://a.com"}, config_path=str(cfg_file))
    # File should exist; permissions unchanged from default (no assertion on exact mode)
    assert cfg_file.exists()


# --- update_config ---

def test_update_config_merges_existing(tmp_path: Path) -> None:
    cfg_file = tmp_path / "config.yaml"
    write_config({"url": "https://old.com", "token": "old-token"}, config_path=str(cfg_file))
    update_config({"url": "https://new.com"}, config_path=str(cfg_file))
    data = yaml.safe_load(cfg_file.read_text())
    assert data["url"] == "https://new.com"
    assert data["token"] == "old-token"


def test_update_config_skips_none_values(tmp_path: Path) -> None:
    cfg_file = tmp_path / "config.yaml"
    write_config({"url": "https://old.com"}, config_path=str(cfg_file))
    update_config({"url": None, "token": "new-token"}, config_path=str(cfg_file))
    data = yaml.safe_load(cfg_file.read_text())
    assert data["url"] == "https://old.com"
    assert data["token"] == "new-token"
