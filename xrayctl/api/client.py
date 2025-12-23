from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

from xrayctl.errors import XrayHTTPError


@dataclass
class XrayClient:
    base_url: str
    token: str
    timeout: int = 30
    project: Optional[str] = None

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def request(self, method: str, path: str, *, json_body: Optional[dict] = None, params: Optional[dict] = None) -> Any:
        url = self.base_url.rstrip("/") + path
        resp = requests.request(
            method=method,
            url=url,
            headers=self._headers(),
            json=json_body,
            params=params,
            timeout=self.timeout,
        )

        # Best-effort response parsing
        try:
            data = resp.json()
        except ValueError:
            data = resp.text

        if resp.status_code >= 400:
            msg = None
            if isinstance(data, dict):
                msg = data.get("error") or data.get("message")
            raise XrayHTTPError(
                message=msg or f"HTTP {resp.status_code}",
                status_code=resp.status_code,
                details=data,
            )

        return data
