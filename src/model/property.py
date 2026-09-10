"""
Roblox property representation.
"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class RobloxProperty:
    name: str
    type_name: str
    value: Any
    raw: Optional[Any] = None

    def to_json_value(self) -> Any:
        """Converts the property value to a JSON-serializable representation."""
        if hasattr(self.value, "to_json"):
            return self.value.to_json()
        return self.value
