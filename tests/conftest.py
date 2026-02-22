from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from xrayctl.api.client import XrayClient


@pytest.fixture
def client() -> XrayClient:
    return XrayClient(base_url="https://xray.example.com", token="test-token")


@pytest.fixture
def client_with_project() -> XrayClient:
    return XrayClient(base_url="https://xray.example.com", token="test-token", project="my-project")


@pytest.fixture
def mock_client() -> MagicMock:
    c = MagicMock(spec=XrayClient)
    c.project = None
    return c


@pytest.fixture
def mock_client_with_project() -> MagicMock:
    c = MagicMock(spec=XrayClient)
    c.project = "my-project"
    return c
