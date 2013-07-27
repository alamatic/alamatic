
import unittest
from alamatic.types import *


class TestTypes(unittest.TestCase):

    def test_type_tests(self):
        self.assertTrue(
            is_our_type(Int32)
        )
        self.assertFalse(
            is_our_type(int)
        )
        self.assertTrue(
            is_our_value(Int32(1))
        )
        self.assertFalse(
            is_our_value(1)
        )
        self.assertFalse(
            is_our_type(Int32(1))
        )
        self.assertFalse(
            is_our_value(Int32)
        )

    def test_integers(self):
        self.assertEqual(
            UInt64.get_limits(),
            (
                0L,
                18446744073709551615L,
            ),
        )
        self.assertEqual(
            Int64.get_limits(),
            (
                -9223372036854775808L,
                9223372036854775807L,
            ),
        )
        self.assertEqual(
            UInt32.get_limits(),
            (
                0L,
                4294967295L,
            ),
        )
        self.assertEqual(
            Int32.get_limits(),
            (
                -2147483648L,
                2147483647L,
            ),
        )
        self.assertEqual(
            UInt16.get_limits(),
            (
                0L,
                65535L,
            ),
        )
        self.assertEqual(
            Int16.get_limits(),
            (
                -32768L,
                32767L,
            ),
        )
        self.assertEqual(
            UInt8.get_limits(),
            (
                0L,
                255L,
            ),
        )
        self.assertEqual(
            Int8.get_limits(),
            (
                -128L,
                127L,
            ),
        )

        self.assertEqual(
            Int8(127).value,
            127L,
        )
        self.assertEqual(
            Int8(-128).value,
            -128L,
        )
        self.assertEqual(
            UInt8(255).value,
            255L,
        )
        self.assertEqual(
            UInt8(0).value,
            0L,
        )
        self.assertRaises(
            Exception,
            lambda: Int8(128),
        )
        self.assertRaises(
            Exception,
            lambda: Int8(-129),
        )
        self.assertRaises(
            Exception,
            lambda: UInt8(257),
        )
        self.assertRaises(
            Exception,
            lambda: UInt8(-1),
        )
