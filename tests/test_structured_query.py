import unittest
from rooman.structured_query import parse


class TestParse(unittest.TestCase):
    def assertParseResult(self, query_str, expected_result):
        result = parse(query_str)
        self.assertEqual(result, expected_result)

    def test_dictionary(self):
        self.assertParseResult('abc=def&g=h', {
            'abc': 'def', 'g': 'h'})

    def test_array(self):
        self.assertParseResult('a=a0&a=a1&a=a2', {
            'a': ['a0', 'a1', 'a2']})

    def test_array_with_brackets(self):
        self.assertParseResult('a[]=a0&a[]=a1&a[]=a2', {
            'a': ['a0', 'a1', 'a2']})

    def test_array_with_index(self):
        self.assertParseResult('a[4]=a4&a[0]=a0&a[3]=a3', {
            'a': ['a0', 'a3', 'a4']})

    def test_number_in_key_dictionary(self):
        self.assertParseResult('a[0]=a0&a[b]=ab&a[1]=a1', {
            'a': {'0': 'a0', 'b': 'ab', '1': 'a1'}})

    def test_nesting_array(self):
        self.assertParseResult('a[1][a]=a1a&a[0][b]=a0b&a[0][a]=a0a&a[1][b]=a1b', {
            'a': [{'a': 'a0a', 'b': 'a0b'}, {'a': 'a1a', 'b': 'a1b'}]})

    def test_top_level_array(self):
        self.assertParseResult('=0&=1&=2&=3', [
            '0', '1', '2', '3'])

    def test_top_level_array_with_index(self):
        self.assertParseResult('1=1&4=4&2=2&7=7', [
            '1', '2', '4', '7'])

    def test_one_element_array(self):
        self.assertParseResult('a[]=a0', {
            'a': ['a0']})

    def test_list_input_form(self):
        self.assertParseResult((
            (r'a', 'a'),
            (r'c[a]', 'ca0'),
            (r'b', 'b0'),
            (r'b', 'b1'),
            (r'c[a]', 'ca1'),
        ), {
            'a': 'a', 'b': ['b0', 'b1'], 'c': {'a': ['ca0', 'ca1']}
        })

    def test_escaped_key_dictionary(self):
        self.assertParseResult((
            (r'ab\[cd\]', 'ab[cd]'),
            (r'\"abcde\"', '"abcde"'),
        ), {
            'ab[cd]': 'ab[cd]', '"abcde"': '"abcde"',
        })

    def test_quoted_key_dictionary(self):
        self.assertParseResult((
            ('"abcd"', 'abcd'),
            ('"abc[def]"', 'abc[def]'),
        ), {
            'abcd': 'abcd', 'abc[def]': 'abc[def]',
        })

    def test_quoted_number_key_dictionary(self):
        self.assertParseResult((
            (r'a["0"]', 'a0'),
            (r'a["1"]', 'a1'),
        ), {
            'a': {'0': 'a0', '1': 'a1'},
        })

    def test_quoted_empty_string_key_dictionary(self):
        self.assertParseResult((
            (r'a[""]', 'a'),
        ), {
            'a': {'': 'a'},
        })

    def test_number_value_type(self):
        self.assertParseResult((
            (r'n:a', '43'),
            (r'n:b', '-100'),
            (r'n:c', '12.3'),
        ), {
            'a': 43, 'b': -100, 'c': 12.3,
        })

    def test_boolean_value_type(self):
        self.assertParseResult((
            (r'b:a', 'true'),
            (r'b:b', 'false'),
        ), {
            'a': True, 'b': False,
        })

    def test_null_value_type(self):
        self.assertParseResult((
            (r'u:a', ''),
            (r'u:b', 'abcd'),
        ), {
            'a': None, 'b': None,
        })

    def test_empty_dictionary_value_type(self):
        self.assertParseResult((
            (r'o:a', ''),
        ), {
            'a': {},
        })

    def test_empty_array_value_type(self):
        self.assertParseResult((
            (r'a:a', ''),
        ), {
            'a': [],
        })

    def test_top_level_empty_dictionary(self):
        self.assertParseResult({
        }, {
        })

    def test_top_level_empty_array(self):
        self.assertParseResult((
            ('^a:', ''),
        ), [])

    def test_top_level_string(self):
        self.assertParseResult((
            ('^s:', 'abcdefg'),
        ), 'abcdefg')

    def test_top_level_number(self):
        self.assertParseResult((
            ('^n:', '1234'),
        ), 1234)

    def test_top_level_boolean(self):
        self.assertParseResult((
            ('^b:', 'true'),
        ), True)

    def test_top_level_null(self):
        self.assertParseResult((
            ('^u:', ''),
        ), None)

    def test_quoted_and_unquoted_mixed_key_dictionary(self):
        self.assertParseResult((
            ('a[0]', 'a00'),
            ('a["0"]', 'a01'),
            ('b["0"]', 'b00'),
            ('b[0]', 'b01'),
        ), {
            'a': {'0': ['a00', 'a01']},
            'b': {'0': ['b00', 'b01']},
        })

    def test_complex_object(self):
        cases = (
        )
        for s, result in cases:
            with self.subTest(query_str=s):
                self.assertEqual(parse(s), result)
