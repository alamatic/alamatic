
import unittest
from alamatic.diagnostics.internals import (
    formatter,
    RangeLink,
    LocationLink,
)
import alamatic.diagnostics.internals as internals


class TestDiagnosticsFormatter(unittest.TestCase):

    def assertFormatPartsResult(self, input, kwargs, expected):
        got = tuple(formatter.vformat_parts(input, kwargs))
        self.assertEqual(got, expected)

    def test_plain_text(self):
        self.assertFormatPartsResult(
            'Hello world',
            {},
            ('Hello world',)
        )

    def test_just_interpolation(self):
        self.assertFormatPartsResult(
            '{food}',
            {"food": "cheese"},
            ('cheese',)
        )

    def test_initial_interpolation(self):
        self.assertFormatPartsResult(
            '{food} pizza',
            {"food": "cheese"},
            ('cheese', ' pizza')
        )

    def test_trailing_interpolation(self):
        self.assertFormatPartsResult(
            'cheese {food}',
            {"food": "pizza"},
            ('cheese ', 'pizza')
        )

    def test_middle_interpolation(self):
        self.assertFormatPartsResult(
            'Hello {name}!',
            {"name": "world"},
            ('Hello ', 'world', '!')
        )

    def test_range_link(self):
        from alamatic.scanner import SourceRange, SourceLocation

        source_range = SourceRange(
            SourceLocation('foo', 1, 1),
            SourceLocation('bar', 2, 2),
        )

        self.assertFormatPartsResult(
            'Error at {source_range:link(some place)}',
            {"source_range": source_range},
            ('Error at ', RangeLink(source_range, 'some place'))
        )

    def test_location_link(self):
        from alamatic.scanner import SourceLocation

        source_location = SourceLocation('foo', 1, 1)

        self.assertFormatPartsResult(
            'Error at {source_location:link(some place)}',
            {"source_location": source_location},
            ('Error at ', LocationLink(source_location, 'some place'))
        )

    #def test_token_conversion(self):
    #    self.assertFormatPartsResult(
    #        'Expected {expected_token!token}',
    #        {"expected_token": ['NEWLINE', '']},
    #        ('Expected ', 'newline')
    #    )
