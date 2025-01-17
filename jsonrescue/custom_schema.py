import logging as l
from typing import Any, List, Dict
from dataclasses import dataclass, field


@dataclass
class Schema:
    type: str  # e.g., 'object', 'array', 'string', 'number', ...
    properties: Dict[str, Any] = field(default_factory=dict)
    items: Any = None  # For array schemas
    required: List[str] = field(default_factory=list)

    def validated(self, data: Any) -> Any:
        original_data = data  # Keep original for debugging

        # OBJECT TYPE
        if self.type == 'object':
            if isinstance(data, list):
                if not data:
                    return None
                data = data[0]

            if not isinstance(data, dict):
                return None

            # Check required fields
            if self.required:
                missing_fields = [key for key in self.required if key not in data]
                if missing_fields:
                    l.log(l.DEBUG, f"Validation failed: Missing required fields {missing_fields} in data {original_data}")
                    return None
            else:
                # If no 'required', ensure at least one known property is present
                if not any(key in data for key in self.properties.keys()):
                    l.log(l.DEBUG, f"Validation failed: No properties found in data {original_data}")
                    return None

            # Recursively validate properties if present
            for key, sub_schema in self.properties.items():
                if key in data:
                    value = sub_schema.validated(data[key])
                    if value is None:
                        l.log(l.DEBUG, f"Validation failed: sub-Schema validation failed for '{key}' = {data[key]}")
                        return None
                    else:
                        data[key] = value
            return data

        # ARRAY TYPE
        elif self.type == 'array':
            if isinstance(data, dict):
                data = list(data.values()) if data else None
                if data:
                    data = data[0]
                else:
                    return None

            if not isinstance(data, list):
                return None

            if self.items:
                for item in data:
                    if not self.items.validated(item):
                        return None
            return data

        # BASIC TYPE CHECKS
        else:
            type_map = {
                'string': str,
                'number': (int, float),
                'boolean': bool,
                'null': type(None)
            }
            accepted_type = type_map.get(self.type, object)
            if not isinstance(data, accepted_type) and isinstance(data, str):
                try:
                    # Handle tuple case explicitly for number conversion
                    if self.type == 'number':
                        accepted_type = float if '.' in data else int
                    return accepted_type(data)
                except TypeError:
                    return None
            else:
                return data


