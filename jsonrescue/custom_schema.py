import logging as logger
from typing import Any, List, Dict
from dataclasses import dataclass, field


class SchemaType:
    OBJECT = dict
    ARRAY = list
    STRING = str
    NUMBER = (int, float)
    BOOLEAN = bool
    NULL = type(None)


@dataclass
class Schema:
    type: type[dict] | type[list] | type[str] | type[float] | type[int] | type[bool] | type[None]
    properties: Dict[str, Any] = field(default_factory=dict)
    items: Any = None  # For array schemas
    required: List[str] = field(default_factory=list)

    def validated(self, data: Any) -> Any:
        original_data = data  # Keep original for debugging

        # OBJECT TYPE
        if self.type == SchemaType.OBJECT:
            # if data is formatted as an array, but an object is expected
            if isinstance(data, SchemaType.ARRAY):
                if not data:
                    return None
                data = data[0]

            if not isinstance(data, self.type):
                return None

            # Check required fields
            if self.required:
                missing_fields = [key for key in self.required if key not in data]
                if missing_fields:
                    logger.log(
                        logger.DEBUG,
                        f"Validation failed: Missing required fields {missing_fields} in data {original_data}"
                    )
                    return None
            else:
                # If no 'required', ensure at least one known property is present
                if not any(key in data for key in self.properties.keys()):
                    logger.log(logger.DEBUG, f"Validation failed: No properties found in data {original_data}")
                    return None

            # Recursively validate properties if present
            for key, sub_schema in self.properties.items():
                if key in data:
                    value = sub_schema.validated(data[key])
                    if value is None:
                        logger.log(
                            logger.DEBUG,
                            f"Validation failed: sub-Schema validation failed for '{key}' = {data[key]}"
                        )
                        return None
                    else:
                        data[key] = value
            return data

        # ARRAY TYPE
        elif self.type == SchemaType.ARRAY:
            # if data is formatted as an object, but an array is expected
            if isinstance(data, SchemaType.OBJECT):
                if not data:
                    return None
                data = [data]

            if not isinstance(data, self.type):
                return None

            if self.items:
                for item in data:
                    if not self.items.validated(item):
                        return None
            return data

        # BASIC TYPE CHECKS
        else:
            class_type = self.type
            if not isinstance(data, class_type) and isinstance(data, str):
                try:
                    # Handle tuple case explicitly for number conversion
                    if self.type == SchemaType.NUMBER:
                        class_type = float if '.' in data else int
                    return class_type(data)
                except TypeError:
                    return None
            else:
                return data
