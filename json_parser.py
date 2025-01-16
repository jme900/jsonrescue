import json
import regex
import re
from typing import Any, List, Dict
from json.decoder import JSONDecodeError
from dataclasses import dataclass, field

_JSON_PATTERN = r"""
    (?P<BRACE_BRACKET>
        \{
            (?: [^{}] | (?&BRACE_BRACKET) )*
        \}
        |
        \[
            (?: [^\[\]] | (?&BRACE_BRACKET) )*
        \]
    )
"""
BRACE_BRACKET = regex.compile(_JSON_PATTERN, regex.VERBOSE | regex.MULTILINE)


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
                    print(f"Validation failed: Missing required fields {missing_fields} in data {original_data}")
                    return None
            else:
                # If no 'required', ensure at least one known property is present
                if not any(key in data for key in self.properties.keys()):
                    print(f"Validation failed: No properties found in data {original_data}")
                    return None

            # Recursively validate properties if present
            for key, sub_schema in self.properties.items():
                if key in data:
                    value = sub_schema.validated(data[key])
                    if value is None:
                        print(f"Validation failed: sub-Schema validation failed for '{key}' = {data[key]}")
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


class JSONParser:
    def __init__(self, schema: Schema):
        self.schema = schema

    def parse(self, text: str) -> Any:
        json_candidates = self.extract_json_candidates(text)
        for candidate in json_candidates:
            fixed_json = self.fix_json(candidate)
            if not fixed_json:
                continue
            try:
                loaded = json.loads(fixed_json)
                validated_data = self.schema.validated(loaded)
                if validated_data is not None:
                    return validated_data
            except JSONDecodeError:
                continue

        raise ValueError("No matching JSON object found.")

    def extract_json_candidates(self, text: str) -> List[str]:
        """
        Extract potential JSON-like substrings from the text using a bracket-matching regex.
        Falls back to fixing the entire text if no well-formed bracket pair is found.
        """
        candidates = BRACE_BRACKET.findall(text)
        if not candidates:
            # Return a list containing the entire text with ensured brackets
            return [self.ensure_ending_brackets(text)]
        return candidates

    def fix_json(self, json_str: str) -> str:
        """ Sequentially attempt fixes on a JSON candidate. """
        json_str = self.fix_keys(json_str)
        # Fix unquoted string values (now handles multi-word)
        json_str = self.fix_string_values(json_str)
        # Escape illegal characters (including inner double quotes)
        json_str = self.escape_illegal_characters(json_str)
        # Ensure brackets are closed properly
        json_str = self.ensure_ending_brackets(json_str)
        # Insert missing commas between objects/arrays
        json_str = self.insert_missing_commas(json_str)
        return json_str

    @staticmethod
    def fix_keys(json_str: str) -> str:
        """Add quotes around unquoted object keys."""
        pattern = re.compile(r'([{,]\s*)([A-Za-z0-9_]+)\s*:')

        def replace(match):
            prefix = match.group(1)
            key = match.group(2)

            # If key is already quoted with single or double quotes, replace with double quotes
            if key.startswith("'") and key.endswith("'"):
                # Remove single quotes and add double quotes
                quoted_key = f'"{key[1:-1]}"'
            elif key.startswith('"') and key.endswith('"'):
                # Already in double quotes, no change needed
                quoted_key = key
            else:
                # Wrap unquoted key in double quotes
                quoted_key = f'"{key}"'

            return f'{prefix}{quoted_key}:'

        fixed_json_str = pattern.sub(replace, json_str)
        return fixed_json_str

    @staticmethod
    def fix_string_values(json_str: str) -> str:
        """
        Add quotes around unquoted string values, allowing for multi-word tokens.
        This finds substrings after a colon that appear before a comma, brace, or bracket.
        """
        pattern = re.compile(r'(:\s*)([^{\[\]",}\]\s][^,\]}]*)')

        def replace(match):
            prefix = match.group(1)
            value = match.group(2).strip()

            # Check if value is valid JSON literal (true, false, null) or a number
            if re.match(r'^(true|false|null)$', value):
                return prefix + value
            if re.match(r'^-?\d+(\.\d+)?$', value):
                return prefix + value
            # In single quotes?
            if value.startswith("'") and value.endswith("'"):
                return prefix + f"\"{value[1:-1]}\""
            # Already in quotes?
            if value.startswith('"') and value.endswith('"'):
                return prefix + value

            # Otherwise, wrap in quotes
            return prefix + f'"{value}"'

        return pattern.sub(replace, json_str)

    @staticmethod
    def escape_illegal_characters(json_str: str) -> str:
        """
        Escape problematic characters (newlines, tabs, backslashes, plus internal quotes).
        """
        # Escape backslashes first
        json_str = json_str.replace('\\', '\\\\')
        # Escape common control characters
        json_str = json_str.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')

        # Escape unescaped double quotes inside strings
        result = []
        length = len(json_str)
        in_string = False
        i = 0

        while i < length:
            char = json_str[i]
            if char == '"':
                if not in_string:
                    # Not in a string, so this quote starts one
                    in_string = True
                    result.append('"')
                else:
                    # Already in a string; decide if this quote ends or should be escaped
                    # Look ahead for next non-whitespace
                    j = i + 1
                    while j < length and json_str[j].isspace():
                        j += 1

                    if j >= length or json_str[j] in [':', ',', '}', ']']:
                        # Valid end of string
                        in_string = False
                        result.append('"')
                    else:
                        # Embedded quote -> escape it
                        result.append('\\"')
            else:
                # Normal character, just add it
                result.append(char)

            i += 1

        return "".join(result)

    @staticmethod
    def ensure_ending_brackets(json_str: str) -> str:
        """
        Add missing closing brackets/braces to a JSON-like string.
        """
        stack = []
        opening_brackets = {'{': '}', '[': ']'}
        closing_brackets = {'}': '{', ']': '['}
        result = []
        in_string = False
        escape = False

        for char in json_str:
            result.append(char)
            if escape:
                escape = False
                continue
            if char == '\\':
                escape = True
                continue
            if char == '"' or char == "'":
                if not in_string:
                    in_string = char
                elif in_string == char:
                    in_string = False
                continue

            if in_string:
                continue

            if char in opening_brackets:
                stack.append(char)
            elif char in closing_brackets:
                if stack and stack[-1] == closing_brackets[char]:
                    stack.pop()
                else:
                    # Mismatched closing bracket, remove it
                    result.pop()

        # Close any unclosed brackets
        while stack:
            opening = stack.pop()
            result.append(opening_brackets[opening])

        return ''.join(result)

    @staticmethod
    def insert_missing_commas(json_str: str) -> str:
        """
        Insert commas between adjacent objects/arrays and between key-value pairs
        if missing.
        """
        # Insert commas between adjacent objects
        json_str = re.sub(r'}\s*{', '},{', json_str)
        # Insert commas between adjacent arrays
        json_str = re.sub(r'\]\s*\[', '],[', json_str)

        # Insert comma between a value and the next key, if missing
        # e.g. "... value "next_key": ..." -> "... value, "next_key": ..."
        json_str = re.sub(r'(":\s*[^",{}\[\]]+)\s*"(\w+)":', r'\1, "\2":', json_str)

        return json_str
