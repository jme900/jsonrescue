import unittest
from json_parser import JSONParser, Schema

parser_with_schema = JSONParser(Schema(
    type='object',
    properties={
        'name': Schema(type='string'),
        'age': Schema(type='number'),
        'emails': Schema(type='array', items=Schema(type='string'))
    },
    required=['name', 'age'],
))
parser_without_schema = JSONParser(Schema(
    type='object',
    properties={
        'name': Schema(type='string'),
        'age': Schema(type='number'),
        'emails': Schema(type='array', items=Schema(type='string'))
    },
))


class TestJSONLikeParser(unittest.TestCase):
    def test_proper_json(self):
        input_text = '{"name": "John Doe", "age": 30, "emails": ["john@example.com"]}'
        expected = {"name": "John Doe", "age": 30, "emails": ["john@example.com"]}
        self.assertEqual(parser_with_schema.parse(input_text), expected)

    def test_missing_required_field(self):
        input_text = '{"name": "Test", "emails": ["test@example.com"]}'
        self.assertIsNone(parser_with_schema.parse(input_text))

    def test_no_required_fields(self):
        input_text = '{"name": "Test", "emails": ["test@example.com"]}'
        expected = {"name": "Test", "emails": ["test@example.com"]}
        self.assertEqual(parser_without_schema.parse(input_text), expected)

    def test_json_with_surrounding_text(self):
        input_text = 'Here is the data: {"name": "Jane", "age":25, "emails":["jane@example.com"]} Thanks!'
        expected = {"name": "Jane", "age": 25, "emails": ["jane@example.com"]}
        self.assertEqual(parser_with_schema.parse(input_text), expected)

    def test_array_input(self):
        input_text = '[{"name": "Alice", "age": 28, "emails": ["alice@example.com"]}]'
        expected = {"name": "Alice", "age": 28, "emails": ["alice@example.com"]}
        self.assertEqual(parser_with_schema.parse(input_text), expected)

    def test_multiple_objects(self):
        input_text = ('{"name":"Charlie","age":40,"emails":["charlie@example.com"]}{"name":"Dana","age":27,"emails":['
                      '"dana@example.com"]}')
        expected = {"name": "Charlie", "age": 40, "emails": ["charlie@example.com"]}
        self.assertEqual(parser_with_schema.parse(input_text), expected)
        input_text = ('{"name":"Charlie","age":40,"emails":["charlie@example.com"]},{"name":"Dana","age":27,"emails":['
                      '"dana@example.com"]}')
        self.assertEqual(parser_with_schema.parse(input_text), expected)

    def test_missing_quotes(self):
        input_text = '{"name": "John Doe", "age": 22, \'emails\': ["john.doe@example.com"], "test": Hello World}'
        expected = {"name": "John Doe", "age": 22, "emails": ["john.doe@example.com"], "test": "Hello World"}
        self.assertEqual(parser_with_schema.parse(input_text), expected)
        # input_text = '{name: "John Doe", \"age\": 22, \'emails\': ["john.doe@example.com"]}'
        # self.assertEqual(parser_with_schema.parse(input_text), expected)

    def test_missing_closing_bracket(self):
        input_text = 'Start {"name": "Bob", "age": 35, "emails": ["bob@example.com"'
        expected = {"name": "Bob", "age": 35, "emails": ["bob@example.com"]}
        self.assertEqual(parser_with_schema.parse(input_text), expected)

    def test_incomplete_array(self):
        input_text = '[{"name": "Frank", "age": 33, "emails": ["frank@example.com"]'
        expected = {"name": "Frank", "age": 33, "emails": ["frank@example.com"]}
        self.assertEqual(parser_with_schema.parse(input_text), expected)


if __name__ == '__main__':
    unittest.main()
