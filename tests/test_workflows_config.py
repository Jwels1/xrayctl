from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from xrayctl.config import write_config
from xrayctl.workflows.config import init_config, save_from_flags, set_value, view_effective


# ---------------------------------------------------------------------------
# init_config
# ---------------------------------------------------------------------------

def test_init_config_creates_file_when_not_exists(tmp_path: Path) -> None:
    cfg_path = str(tmp_path / "config.yaml")
    result = init_config(cfg_path)
    assert result["ok"] is True
    assert Path(result["path"]).exists()


def test_init_config_returns_error_when_exists(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("url: https://existing.com\n")
    result = init_config(str(cfg_path))
    assert result["ok"] is False
    assert "already exists" in result["error"]


def test_init_config_does_not_overwrite_existing(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("url: https://existing.com\n")
    init_config(str(cfg_path))
    assert cfg_path.read_text() == "url: https://existing.com\n"


# ---------------------------------------------------------------------------
# set_value
# ---------------------------------------------------------------------------

def test_set_value_updates_string_key(tmp_path: Path) -> None:
    cfg_path = str(tmp_path / "config.yaml")
    write_config({"url": None}, config_path=cfg_path)
    result = set_value(cfg_path, "url", "https://new.com")
    assert result["ok"] is True
    assert result["updated"]["url"] == "https://new.com"


def test_set_value_coerces_timeout_to_int(tmp_path: Path) -> None:
    cfg_path = str(tmp_path / "config.yaml")
    write_config({}, config_path=cfg_path)
    result = set_value(cfg_path, "timeout", "60")
    assert result["updated"]["timeout"] == 60
    assert isinstance(result["updated"]["timeout"], int)


def test_set_value_raises_on_unknown_key(tmp_path: Path) -> None:
    cfg_path = str(tmp_path / "config.yaml")
    with pytest.raises(ValueError, match="Unsupported key"):
        set_value(cfg_path, "unknown_key", "value")


# ---------------------------------------------------------------------------
# save_from_flags
# ---------------------------------------------------------------------------

def test_save_from_flags_saves_provided_url(tmp_path: Path) -> None:
    cfg_path = str(tmp_path / "config.yaml")
    args = argparse.Namespace(
        url="https://a.com", token=None, project=None, timeout=None, format=None, config=cfg_path
    )
    result = save_from_flags(args)
    assert result["ok"] is True
    assert result["saved"]["url"] == "https://a.com"


def test_save_from_flags_redacts_token(tmp_path: Path) -> None:
    cfg_path = str(tmp_path / "config.yaml")
    args = argparse.Namespace(
        url=None, token="super-secret", project=None, timeout=None, format=None, config=cfg_path
    )
    result = save_from_flags(args)
    assert result["saved"]["token"] == "***"


def test_save_from_flags_only_saves_provided_flags(tmp_path: Path) -> None:
    cfg_path = str(tmp_path / "config.yaml")
    args = argparse.Namespace(
        url="https://a.com", token=None, project=None, timeout=None, format=None, config=cfg_path
    )
    result = save_from_flags(args)
    assert "token" not in result["saved"]
    assert "project" not in result["saved"]


def test_save_from_flags_raises_when_no_flags_provided(tmp_path: Path) -> None:
    cfg_path = str(tmp_path / "config.yaml")
    args = argparse.Namespace(
        url=None, token=None, project=None, timeout=None, format=None, config=cfg_path
    )
    with pytest.raises(ValueError, match="No flags provided"):
        save_from_flags(args)


# ---------------------------------------------------------------------------
# view_effective
# ---------------------------------------------------------------------------

def test_view_effective_returns_ok_true(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("url: https://a.com\ntoken: secret\ntimeout: 30\nformat: json\n")
    args = argparse.Namespace(
        url=None, token=None, project=None, timeout=None, format=None, config=str(cfg_path)
    )
    result = view_effective(args)
    assert result["ok"] is True


def test_view_effective_omits_token(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("url: https://a.com\ntoken: secret\ntimeout: 30\nformat: json\n")
    args = argparse.Namespace(
        url=None, token=None, project=None, timeout=None, format=None, config=str(cfg_path)
    )
    result = view_effective(args)
    assert "token" not in result["effective"]


def test_view_effective_includes_url(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("url: https://a.com\ntimeout: 30\nformat: json\n")
    args = argparse.Namespace(
        url=None, token=None, project=None, timeout=None, format=None, config=str(cfg_path)
    )
    result = view_effective(args)
    assert result["effective"]["url"] == "https://a.com"
