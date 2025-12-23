from __future__ import annotations
from typing import Any
from xrayctl.api.client import XrayClient


def ping(client: XrayClient) -> Any:
    # This is the common Xray endpoint. If your instance differs,
    # you only change it here.
    return client.request("GET", "/xray/api/v1/system/ping")
