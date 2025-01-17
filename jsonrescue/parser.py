import json
import regex
import re
from typing import Any, List
from json.decoder import JSONDecodeError
from .custom_schema import Schema

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


class Parser:
    def __init__(self, schema: Schema = None):
        self.schema = schema

    def rescue(self, text: str) -> Any:
        try:
            result = json.loads(text)
            return self.schema.validated(result) if self.schema else result
        except JSONDecodeError:
            results = []
            json_candidates = self.extract_json_candidates(text)
            for candidate in json_candidates:
                fixed_json = self.fix_json(candidate)
                if not fixed_json:
                    continue
                try:
                    loaded = json.loads(fixed_json)
                    if self.schema:
                        validated_data = self.schema.validated(loaded)
                        if validated_data is not None:
                            return validated_data
                    else:
                        if isinstance(loaded, list):
                            results.extend(loaded)
                        else:
                            results.append(loaded)
                except JSONDecodeError:
                    continue
            if len(results) > 0:
                return results if len(results) > 1 else results[0]

        return None

    def extract_json_candidates(self, text: str) -> List[str]:
        """
        Extract potential JSON-like substrings from the text using a bracket-matching regex.
        Falls back to fixing the entire text if no well-formed bracket pair is found.
        """
        missing_curly = abs(text.count('{') - text.count('}'))
        missing_square = abs(text.count('[') - text.count(']'))
        if missing_curly > 0 or missing_square > 0:
            # Return a corrected text with ensured brackets
            text = self.ensure_ending_brackets(text)
        candidates = BRACE_BRACKET.findall(text)
        return candidates

    def fix_json(self, json_str: str) -> str:
        """ Sequentially attempt fixes on a JSON candidate. """
        json_str = re.sub(r'\s+', ' ', json_str).strip()
        json_str = self.fix_keys(json_str)
        # Fix unquoted string values (now handles multi-word)
        json_str = self.fix_string_values(json_str)
        # Escape illegal characters (including inner double quotes)
        json_str = self.escape_illegal_characters(json_str)
        # Insert commas between adjacent objects/arrays
        json_str = self.insert_missing_commas(json_str)
        return json_str

    @staticmethod
    def fix_keys(json_str: str) -> str:
        """Add quotes around unquoted object keys."""
        pattern = re.compile(r'([{,]\s*)([A-Za-z0-9_\']+)\s*:')

        def replace(match):
            prefix = match.group(1)
            key = match.group(2)

            # If key is already quoted with single or double quotes, replace with double quotes
            if key.startswith("'") and key.endswith("'"):
                # Remove single quotes and add double quotes
                key = key[1:-1]

            return f'{prefix}"{key}":'

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

        # Close string if still inside one
        if in_string:
            result.append(in_string)

        # Close any unclosed brackets
        while stack:
            opening = stack.pop()
            result.append(opening_brackets[opening])

        return ''.join(result)

    @staticmethod
    def insert_missing_commas(json_str: str) -> str:
        """
        Insert commas between adjacent objects/arrays
        """
        # Insert commas between adjacent objects
        json_str = re.sub(r'}\s*{', '},{', json_str)
        # Insert commas between adjacent arrays
        json_str = re.sub(r'\]\s*\[', '],[', json_str)

        # Insert comma between a value and the next key, if missing
        # e.g. "... value "next_key": ..." -> "... value, "next_key": ..."
        # json_str = re.sub(r'(":\s*[^",{}\[\]]+)\s*"(\w+)":', r'\1, "\2":', json_str)

        return json_str

