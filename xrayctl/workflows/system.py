from __future__ import annotations
from typing import Any, Dict

from xrayctl.api.client import XrayClient
from xrayctl.api import system as system_api


def ping(client: XrayClient) -> Dict[str, Any]:
    data = system_api.ping(client)
    return {"ok": True, "response": data}
