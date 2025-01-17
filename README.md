# JSONRescue

## Overview

`JSONRescue` is a robust Python library designed to parse and repair malformed JSON-like text, specifically targeting common errors found in AI model responses that fail to return valid JSON. The library employs heuristics to identify, fix, and validate JSON structures against a provided schema, ensuring data consistency and correctness.

## Features

- **Bracket Matching and Extraction:** Uses advanced regex patterns to identify JSON-like structures within a text, even when nested.
- **Schema Validation:** Ensures the parsed JSON adheres to a defined schema using a customizable `Schema` class.
- **Error Recovery:** Attempts to fix common JSON errors, including:
  - Missing or unquoted keys.
  - Unquoted or improperly formatted string values.
  - Missing or extra brackets.
  - Escaping illegal characters.
- **Customizable Fixes:** Implements modular methods for fixing specific JSON issues.

## Installation

```bash
pip install regex
```

## Usage

### Example

```python
from custom_schema import Schema
from json_rescue import JSONRescue

# Define a schema for validation
schema = Schema(
    type='object',
    properties={
        'name': Schema(type='string'),
        'age': Schema(type='number'),
        'emails': Schema(type='array', items=Schema(type='string'))
    },
    required=['name', 'age']
)

parser = JSONRescue(schema)

malformed_json = """
{
    name: John Doe,
    age: 30,
    emails: ['john@example.com']
}
"""

parsed_data = parser.rescue(malformed_json)

if parsed_data:
    print("Valid JSON:", parsed_data)
else:
    print("Failed to parse JSON")
```

### Examples of Errors Handled

1. **Missing Quotes Around Keys or Values:**
   - Input: `{name: John Doe, age: 22}`
   - Output: `{"name": "John Doe", "age": 22}`

2. **Escaped Illegal Characters:**
   - Input: `{ "name": "John \"Doe\"", "age": 30}`
   - Output: `{ "name": "John \"Doe\"", "age": 30}`

3. **Fixing Missing Brackets:**
   - Input: `{"name": "Jane"`
   - Output: `{ "name": "Jane" }`

4. **Handling Multiple Objects in Text:**
   - Input: `Here is {"name": "Dana", "age": 27}{"name": "Chris", "age": 35}`
   - Output: `{"name": "Dana", "age": 27}` (First valid object parsed)

5. **Unquoted String Values:**
   - Input: `{"key": Value, "number": 123}`
   - Output: `{"key": "Value", "number": 123}`

## Key Components

### Class: `JSONRescue`

#### Initialization

```python
JSONRescue(schema: Schema)
```
- **schema:** An instance of the `Schema` class defining the expected JSON structure.

#### Methods

1. **`rescue(text: str) -> Any`**
   - Attempts to parse the input text as JSON.
   - Validates against the provided schema.

2. **`extract_json_candidates(text: str) -> List[str]`**
   - Extracts potential JSON substrings from the input text using a bracket-matching regex.

3. **`fix_json(json_str: str) -> str`**
   - Applies a sequence of fixes to a JSON string.

4. **`fix_keys(json_str: str) -> str`**
   - Quotes unquoted object keys.

5. **`fix_string_values(json_str: str) -> str`**
   - Quotes unquoted string values.

6. **`escape_illegal_characters(json_str: str) -> str`**
   - Escapes problematic characters like newlines, tabs, and unescaped quotes.

7. **`ensure_ending_brackets(json_str: str) -> str`**
   - Fixes mismatched or missing brackets.

## Advanced Configuration

The library allows customization and extension by overriding its methods for specific JSON-repair scenarios. For example, you can add custom regex patterns or post-processing logic as needed.

## Limitations

- The parser assumes input text contains at least one valid JSON-like structure. Extremely malformed input may result in parsing failures.
- It relies on heuristics to fix errors, which may not always produce the intended results.

## Testing

The project includes a suite of unit tests to validate its functionality. To run the tests:

```bash
python -m unittest test.py
```

### Example Test Cases

- **Proper JSON:**
  ```python
  input_text = '{"name": "John Doe", "age": 30, "emails": ["john@example.com"]}'
  expected = {"name": "John Doe", "age": 30, "emails": ["john@example.com"]}
  ```

- **Missing Required Field:**
  ```python
  input_text = '{"name": "Test", "emails": ["test@example.com"]}'
  assert parser_with_schema.rescue(input_text) is None
  ```

- **Incomplete Brackets:**
  ```python
  input_text = 'Start {"name": "Bob", "age": 35, "emails": ["bob@example.com"'
  expected = {"name": "Bob", "age": 35, "emails": ["bob@example.com"]}
  ```

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License.

