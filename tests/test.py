import unittest
from jsonrescue.parser import Parser
from jsonrescue.custom_schema import Schema, SchemaType

schema_with_requirements = Schema(
    type=SchemaType.OBJECT,
    properties={
        'name': Schema(type=SchemaType.STRING),
        'age': Schema(type=SchemaType.NUMBER),
        'emails': Schema(type=SchemaType.ARRAY, items=Schema(type=SchemaType.STRING))
    },
    required=['name', 'age']
)
schema_without_requirements = Schema(
    type=SchemaType.OBJECT,
    properties={
        'name': Schema(type=SchemaType.STRING),
        'age': Schema(type=SchemaType.NUMBER),
        'emails': Schema(type=SchemaType.ARRAY, items=Schema(type=SchemaType.STRING))
    },
)
# returns a JSON result if any json-like element was found in the text
parser_no_schema = Parser()

# returns a JSON object if all the schema's required properties exist in the text
parser_schema_object_req = Parser(schema_with_requirements)

# returns a JSON object if any of the schema's properties exist in the text
parser_schema_object_no_req = Parser(schema_without_requirements)

# returns a JSON array if each of the item's required properties exist in the text
parser_schema_array_with_item_req = Parser(Schema(
    type=SchemaType.ARRAY,
    items=schema_with_requirements
))

# returns a JSON array if each of the items in the array contain any of the schema's properties within the text
parser_schema_array_with_no_item_req = Parser(Schema(
    type=SchemaType.ARRAY,
    items=schema_without_requirements
))


class TestParser(unittest.TestCase):
    def test_proper_json_object(self):
        input_text = '{"name": "John Doe", "age": 30, "emails": ["john@example.com"]}'
        expected = {"name": "John Doe", "age": 30, "emails": ["john@example.com"]}
        self.assertEqual(parser_schema_object_req.rescue(input_text), expected)
        self.assertEqual(parser_schema_object_no_req.rescue(input_text), expected)
        self.assertEqual(parser_schema_array_with_item_req.rescue(input_text), [expected])
        self.assertEqual(parser_schema_array_with_no_item_req.rescue(input_text), [expected])
        self.assertEqual(parser_no_schema.rescue(input_text), expected)

    def test_proper_json_array(self):
        input_text = '''
        [
            {"name": "John Doe", "age": 30, "emails": ["john@example.com"]},
            {"name": "Alice", "age": 28, "emails": ["alice@example.com"]}
        ]
        '''
        object_expected = {"name": "John Doe", "age": 30, "emails": ["john@example.com"]}
        array_expected = [
            {"name": "John Doe", "age": 30, "emails": ["john@example.com"]},
            {"name": "Alice", "age": 28, "emails": ["alice@example.com"]}
        ]
        self.assertEqual(parser_schema_object_req.rescue(input_text), object_expected)
        self.assertEqual(parser_schema_object_no_req.rescue(input_text), object_expected)
        self.assertEqual(parser_schema_array_with_item_req.rescue(input_text), array_expected)
        self.assertEqual(parser_schema_array_with_no_item_req.rescue(input_text), array_expected)
        self.assertEqual(parser_no_schema.rescue(input_text), array_expected)

    def test_missing_required_field(self):
        input_text = '{"foo": "bar", "emails": ["test@example.com"]}'
        expected = {"foo": "bar", "emails": ["test@example.com"]}
        self.assertIsNone(parser_schema_object_req.rescue(input_text))
        self.assertEqual(parser_schema_object_no_req.rescue(input_text), expected)
        self.assertIsNone(parser_schema_array_with_item_req.rescue(input_text))
        self.assertEqual(parser_schema_array_with_no_item_req.rescue(input_text), [expected])
        self.assertEqual(parser_no_schema.rescue(input_text), expected)

    def test_not_json(self):
        input_text = 'Hello, world!'
        self.assertIsNone(parser_schema_object_req.rescue(input_text))
        self.assertIsNone(parser_schema_object_no_req.rescue(input_text))
        self.assertIsNone(parser_schema_array_with_item_req.rescue(input_text))
        self.assertIsNone(parser_schema_array_with_no_item_req.rescue(input_text))
        self.assertIsNone(parser_no_schema.rescue(input_text))

    def test_json_with_surrounding_text(self):
        input_text = 'Here is the data\n{"name": "Jane", "age":25, "emails":["jane@example.com"]} Thanks!'
        expected = {"name": "Jane", "age": 25, "emails": ["jane@example.com"]}
        self.assertEqual(parser_schema_object_req.rescue(input_text), expected)
        self.assertEqual(parser_schema_object_no_req.rescue(input_text), expected)
        self.assertEqual(parser_schema_array_with_item_req.rescue(input_text), [expected])
        self.assertEqual(parser_schema_array_with_no_item_req.rescue(input_text), [expected])
        self.assertEqual(parser_no_schema.rescue(input_text), expected)

    def test_multiple_objects(self):
        input_text = ('Here\'s a test {"test":"Hello World","foo": "bar"}{"name":"Dana","age":27,"emails":['
                      '"dana@example.com"]}')
        expected = {"name": "Dana", "age": 27, "emails": ["dana@example.com"]}
        full_json_expected = [
            {"test": "Hello World", "foo": "bar"},
            {"name": "Dana", "age": 27, "emails": ["dana@example.com"]},
        ]
        self.assertEqual(parser_schema_object_req.rescue(input_text), expected)
        self.assertEqual(parser_schema_object_no_req.rescue(input_text), expected)
        self.assertEqual(parser_schema_array_with_item_req.rescue(input_text), [expected])
        self.assertEqual(parser_schema_array_with_no_item_req.rescue(input_text), [expected])
        self.assertEqual(parser_no_schema.rescue(input_text), full_json_expected)

    def test_missing_quotes(self):
        input_text = '{"name": John Doe, age: 22, \'emails\': ["john.doe@example.com"], "test": Hello World}'
        expected = {"name": "John Doe", "age": 22, "emails": ["john.doe@example.com"], "test": "Hello World"}
        self.assertEqual(parser_schema_object_req.rescue(input_text), expected)
        self.assertEqual(parser_schema_object_no_req.rescue(input_text), expected)
        self.assertEqual(parser_schema_array_with_item_req.rescue(input_text), [expected])
        self.assertEqual(parser_schema_array_with_no_item_req.rescue(input_text), [expected])
        self.assertEqual(parser_no_schema.rescue(input_text), expected)

    def test_missing_single_ending(self):
        input_text = 'Start {"name": "Bob", "age": 35, "emails": ["bob@example.com'
        expected = {"name": "Bob", "age": 35, "emails": ["bob@example.com"]}
        self.assertEqual(parser_schema_object_req.rescue(input_text), expected)
        self.assertEqual(parser_schema_object_no_req.rescue(input_text), expected)
        self.assertEqual(parser_schema_array_with_item_req.rescue(input_text), [expected])
        self.assertEqual(parser_schema_array_with_no_item_req.rescue(input_text), [expected])
        self.assertEqual(parser_no_schema.rescue(input_text), expected)

    def test_missing_multi_ending(self):
        input_text = 'Hello World [{"name": "Frank", "age": 33, "emails": ["frank@example.com'
        expected = {"name": "Frank", "age": 33, "emails": ["frank@example.com"]}
        self.assertEqual(parser_schema_object_req.rescue(input_text), expected)
        self.assertEqual(parser_schema_object_no_req.rescue(input_text), expected)
        self.assertEqual(parser_schema_array_with_item_req.rescue(input_text), [expected])
        self.assertEqual(parser_schema_array_with_no_item_req.rescue(input_text), [expected])
        self.assertEqual(parser_no_schema.rescue(input_text), expected)

    def test_malformed_array(self):
        input_text = '''
            [
                {"name": "Alice", "age": 28, "emails": ["alice@example.com"]}
                {"name": "Jane", "age":25, "emails":["jane@example.com"]}
            ]
        '''
        expected = [
            {"name": "Alice", "age": 28, "emails": ["alice@example.com"]},
            {"name": "Jane", "age": 25, "emails": ["jane@example.com"]}
        ]
        self.assertEqual(parser_schema_object_req.rescue(input_text), expected[0])
        self.assertEqual(parser_schema_object_no_req.rescue(input_text), expected[0])
        self.assertEqual(parser_schema_array_with_item_req.rescue(input_text), expected)
        self.assertEqual(parser_schema_array_with_no_item_req.rescue(input_text), expected)
        self.assertEqual(parser_no_schema.rescue(input_text), expected)


if __name__ == '__main__':
    unittest.main()
