from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class XrayError(Exception):
    message: str
    details: Optional[Any] = None

    def __str__(self) -> str:
        return self.message


@dataclass
class XrayHTTPError(XrayError):
    status_code: int = 0
