import json
from typing import Any, Literal
import yaml

Format = Literal["json", "yaml"]

def render(obj: Any, fmt: Format = "json") -> str:
    if fmt == "yaml":
        return yaml.safe_dump(obj, sort_keys=False)
    return json.dumps(obj, indent=2, sort_keys=False)

def print_out(obj: Any, fmt: Format = "json") -> None:
    print(render(obj, fmt=fmt))
