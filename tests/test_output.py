from __future__ import annotations

import json

import pytest
import yaml

from xrayctl.output import print_out, render


def test_render_json_parses_back() -> None:
    result = render({"ok": True, "count": 3}, fmt="json")
    assert json.loads(result) == {"ok": True, "count": 3}


def test_render_yaml_parses_back() -> None:
    result = render({"ok": True, "count": 3}, fmt="yaml")
    assert yaml.safe_load(result) == {"ok": True, "count": 3}


def test_render_json_preserves_insertion_order() -> None:
    result = render({"z": 1, "a": 2}, fmt="json")
    keys = list(json.loads(result).keys())
    assert keys == ["z", "a"]


def test_render_json_default_format() -> None:
    result = render({"ok": True})
    json.loads(result)  # must be valid JSON


def test_print_out_json_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    print_out({"ok": True, "msg": "hello"}, fmt="json")
    captured = capsys.readouterr()
    assert json.loads(captured.out) == {"ok": True, "msg": "hello"}


def test_print_out_yaml_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    print_out({"ok": True, "msg": "hello"}, fmt="yaml")
    captured = capsys.readouterr()
    assert yaml.safe_load(captured.out) == {"ok": True, "msg": "hello"}


def test_print_out_list(capsys: pytest.CaptureFixture[str]) -> None:
    print_out([1, 2, 3], fmt="json")
    captured = capsys.readouterr()
    assert json.loads(captured.out) == [1, 2, 3]
