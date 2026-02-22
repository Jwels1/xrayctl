from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from unittest.mock import patch

from xrayctl.main import _get_version


def test_get_version_returns_package_version() -> None:
    with patch("xrayctl.main._pkg_version", return_value="0.1.0"):
        assert _get_version() == "0.1.0"


def test_get_version_returns_unknown_when_not_installed() -> None:
    with patch("xrayctl.main._pkg_version", side_effect=PackageNotFoundError):
        assert _get_version() == "unknown"
