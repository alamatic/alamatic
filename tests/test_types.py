
import unittest
from alamatic.types import *
from alamatic.ast import *
from alamatic.testutil import *


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

    def test_integer_limits(self):
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

    @unittest.skip("needs to be updated to intermediate style")
    def test_integer_arithmetic(self):

        dummy_node = DummyStmtCompileTime('placeholder')

        # For testing the constant folding behavior.
        def assert_binop_value(meth, lhs_value, rhs_value, result_value):
            result = meth(
                ValueExpr(None, lhs_value),
                ValueExpr(None, rhs_value),
            )
            self.assertEqual(
                type(result),
                ValueExpr
            )
            self.assertEqual(
                type(result.value),
                type(result_value),
            )
            self.assertEqual(
                result.value.value,
                result_value.value,
            )

        # For testing our type conversion behavior on variable operands.
        def assert_binop_compile(
            meth, lhs_type, rhs_type,
            result_node_type, result_node_op, result_type,
        ):
            lhs = DummyExprRuntime('lhs', lhs_type)
            rhs = DummyExprRuntime('rhs', rhs_type)
            result = meth(
                lhs,
                rhs,
            )
            self.assertEqual(
                type(result),
                result_node_type,
            )
            self.assertEqual(
                result.op,
                result_node_op,
            )
            self.assertEqual(
                result.result_type,
                result_type,
            )

        assert_binop_value(
            Int8.add,
            Int8(1),
            Int8(2),
            Int8(3),
        )
        assert_binop_value(
            Int8.add,
            Int8(1),
            Int16(2),
            Int16(3),
        )
        assert_binop_value(
            Int8.add,
            Int16(1),
            Int8(2),
            Int16(3),
        )
        assert_binop_value(
            Int8.add,
            UInt8(1),
            UInt8(2),
            UInt8(3),
        )
        assert_binop_value(
            Int8.add,
            UInt8(1),
            Int8(2),
            Int8(3),
        )
        assert_binop_value(
            Int8.add,
            Int8(1),
            UInt8(2),
            Int8(3),
        )

        assert_binop_compile(
            Int8.add,
            Int8,
            Int8,
            result_node_type=SumExpr,
            result_node_op="+",
            result_type=Int8,
        )
        assert_binop_compile(
            Int8.add,
            Int16,
            Int8,
            result_node_type=SumExpr,
            result_node_op="+",
            result_type=Int16,
        )
        assert_binop_compile(
            Int8.add,
            Int8,
            Int16,
            result_node_type=SumExpr,
            result_node_op="+",
            result_type=Int16,
        )
        assert_binop_compile(
            UInt8.add,
            UInt8,
            UInt8,
            result_node_type=SumExpr,
            result_node_op="+",
            result_type=UInt8,
        )
        assert_binop_compile(
            UInt8.add,
            UInt8,
            Int8,
            result_node_type=SumExpr,
            result_node_op="+",
            result_type=Int8,
        )
        assert_binop_compile(
            Int8.add,
            Int8,
            UInt8,
            result_node_type=SumExpr,
            result_node_op="+",
            result_type=Int8,
        )

    def test_bool_construct(self):
        self.assertEqual(
            Bool(True).value,
            True,
        )
        self.assertEqual(
            Bool(False).value,
            False,
        )
        self.assertRaises(
            Exception,
            lambda: Bool(None).value,
        )
        self.assertRaises(
            Exception,
            lambda: Bool(1).value,
        )
        self.assertRaises(
            Exception,
            lambda: Bool("true").value,
        )


class TestValueMerge(unittest.TestCase):

    def test_matching_values(self):
        a = DummyType(5)
        b = DummyType(5)
        m = a.merge(b)

        self.assertEqual(
            type(m),
            DummyType,
        )
        self.assertEqual(
            m.value,
            5,
        )

    def test_same_type_different_value(self):
        a = DummyType(1)
        b = DummyType(2)
        m = a.merge(b)

        self.assertFalse(
            m.value_is_known,
        )
        self.assertEqual(
            m.apparent_type,
            DummyType,
        )

    def test_same_type_unknown_values(self):
        a = Unknown(DummyType)
        b = Unknown(DummyType)
        m = a.merge(b)

        self.assertFalse(
            m.value_is_known,
        )
        self.assertEqual(
            m.apparent_type,
            DummyType,
        )

    def test_unknown_types(self):
        a = Unknown()
        b = Unknown()
        m = a.merge(b)

        self.assertFalse(
            m.value_is_known,
        )
        self.assertEqual(
            m.apparent_type,
            Unknown,
        )

    def test_unknown_type_known_type_upgrade(self):
        a = Unknown()
        b = Unknown(DummyType)
        m = a.merge(b)

        self.assertFalse(
            m.value_is_known,
        )
        self.assertEqual(
            m.apparent_type,
            DummyType,
        )

        m = b.merge(a)

        self.assertFalse(
            m.value_is_known,
        )
        self.assertEqual(
            m.apparent_type,
            DummyType,
        )

    def test_unknown_type_known_value_upgrade(self):
        a = Unknown()
        b = DummyType(2)
        m = a.merge(b)

        self.assertFalse(
            m.value_is_known,
        )
        self.assertEqual(
            m.apparent_type,
            DummyType,
        )

        m = b.merge(a)

        self.assertFalse(
            m.value_is_known,
        )
        self.assertEqual(
            m.apparent_type,
            DummyType,
        )

    def test_known_type_known_value(self):
        a = Unknown(DummyType)
        b = DummyType(2)
        m = a.merge(b)

        self.assertFalse(
            m.value_is_known,
        )
        self.assertEqual(
            m.apparent_type,
            DummyType,
        )

        m = b.merge(a)

        self.assertFalse(
            m.value_is_known,
        )
        self.assertEqual(
            m.apparent_type,
            DummyType,
        )

    def test_type_mismatch(self):
        from alamatic.preprocessor import InappropriateTypeError

        class DummyType2(DummyType):
            pass

        a = Unknown(DummyType)
        b = Unknown(DummyType2)

        self.assertRaises(
            InappropriateTypeError,
            lambda: a.merge(b)
        )
        self.assertRaises(
            InappropriateTypeError,
            lambda: b.merge(a)
        )

        a = DummyType(1)

        self.assertRaises(
            InappropriateTypeError,
            lambda: a.merge(b)
        )
        self.assertRaises(
            InappropriateTypeError,
            lambda: b.merge(a)
        )
