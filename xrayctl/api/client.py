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
        """
        Construct HTTP headers for Xray API requests.

        Returns:
            Dict[str, str]: Headers including Authorization and content type.
        """
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def request(self, method: str, path: str, *, json_body: Optional[dict] = None, params: Optional[dict] = None) -> Any:
        """
        Execute an HTTP request against the Xray API.

        Args:
            method: HTTP method (e.g. 'GET', 'POST').
            path: API path (e.g. '/xray/api/v1/artifacts').
            json_body: Optional JSON body for POST/PUT requests.
            params: Optional query parameters.

        Returns:
            Parsed JSON response, or raw text if response is not JSON.

        Raises:
            XrayHTTPError: If the response status code is >= 400.
        """
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
