
import unittest
import mock
from alamatic.types.integer import *


class TestTypeImpl(unittest.TestCase):

    def test_limits(self):
        self.assertEqual(
            Int8.impl.limits,
            (-128, 127),
        )
        self.assertEqual(
            UInt8.impl.limits,
            (0, 255),
        )
        self.assertEqual(
            Int16.impl.limits,
            (-32768, 32767),
        )
        self.assertEqual(
            UInt16.impl.limits,
            (0, 65535),
        )
        self.assertEqual(
            Int32.impl.limits,
            (-2147483648L, 2147483647L),
        )
        self.assertEqual(
            UInt32.impl.limits,
            (0, 4294967295L),
        )
        self.assertEqual(
            Int64.impl.limits,
            (-9223372036854775808L, 9223372036854775807L),
        )
        self.assertEqual(
            UInt64.impl.limits,
            (0, 18446744073709551615L),
        )

    def test_constrain_value_signed(self):
        self.assertEqual(
            Int8.impl.constrain_value(2),
            2,
        )
        self.assertEqual(
            Int8.impl.constrain_value(-2),
            -2,
        )
        self.assertEqual(
            Int8.impl.constrain_value(127),
            127,
        )
        self.assertEqual(
            Int8.impl.constrain_value(128),
            -128,
        )
        self.assertEqual(
            Int8.impl.constrain_value(255),
            -1,
        )
        self.assertEqual(
            Int8.impl.constrain_value(256),
            0,
        )
        self.assertEqual(
            Int8.impl.constrain_value(-128),
            -128,
        )
        self.assertEqual(
            Int8.impl.constrain_value(-129),
            127,
        )

    def test_constrain_value_unsigned(self):
        self.assertEqual(
            UInt8.impl.constrain_value(2),
            2,
        )
        self.assertEqual(
            UInt8.impl.constrain_value(-2),
            254,
        )
        self.assertEqual(
            UInt8.impl.constrain_value(127),
            127,
        )
        self.assertEqual(
            UInt8.impl.constrain_value(128),
            128,
        )
        self.assertEqual(
            UInt8.impl.constrain_value(255),
            255,
        )
        self.assertEqual(
            UInt8.impl.constrain_value(256),
            0,
        )
        self.assertEqual(
            UInt8.impl.constrain_value(-128),
            128,
        )
        self.assertEqual(
            UInt8.impl.constrain_value(-129),
            127,
        )

    def test_get_llvm_value(self):
        from llvm.core import Type
        # This is a pretty dumb test since it really just repeats
        # the body of the function. So not gonna bother testing every
        # permutation.
        self.assertEqual(
            Int8.impl.get_llvm_type(Type),
            Type.int(8),
        )
        self.assertEqual(
            UInt8.impl.get_llvm_type(Type),
            Type.int(8),
        )

    def test_add_constant(self):

        def add(lhs_value, rhs_value):
            lhs = mock.Mock()
            rhs = mock.Mock()
            lhs.type = Int8
            lhs.constant_value = lhs_value
            rhs.type = Int8
            rhs.constant_value = rhs_value
            return Int8.impl.add.get_constant_result(lhs, rhs)

        self.assertEqual(
            add(2, 2),
            4,
        )
        self.assertEqual(
            # overflow
            add(127, 1),
            -128,
        )
        self.assertEqual(
            # underflow
            add(-128, -1),
            127,
        )
        self.assertEqual(
            # wrap around
            add(127, 256),
            127,
        )
