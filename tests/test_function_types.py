
from alamatic.ast import *
from alamatic.types import *
from alamatic.testutil import *


class TestFunctionTypes(LanguageTestCase):

    def test_get_function_type(self):
        no_args_void = Function((), None, None)
        no_args_void_again = Function((), None, None)
        dummy_arg_void = Function((DummyType,), None, None)
        dummy_arg_void_again = Function((DummyType,), None, None)
        dummy_arg_ret = Function((DummyType,), DummyType, None)
        dummy_arg_ret_except = Function((DummyType,), DummyType, DummyType)
        dummy_arg_except = Function((DummyType,), None, DummyType)
        bool_arg = Function((Bool,), None, None)

        self.assertTrue(
            no_args_void is no_args_void_again,
            "no_args_void and no_args_void_again should be the same object",
        )

        self.assertTrue(
            dummy_arg_void is dummy_arg_void_again,
            "dummy_arg_void and dummy_arg_void_again should be the same",
        )

        all_different = [
            no_args_void,
            dummy_arg_void,
            dummy_arg_ret,
            dummy_arg_ret_except,
            dummy_arg_except,
            bool_arg,
        ]

        for ai, a in enumerate(all_different):
            for bi, b in enumerate(all_different):
                if ai != bi:
                    self.assertTrue(
                        a is not b,
                        "types %i and %i should not be same object" % (
                            ai,
                            bi,
                        )
                    )

    def test_usage(self):
        # TODO: Update this test once the function types actually take
        # some constructor parameters.
        no_args_void_type = Function((), None, None)
        no_args_void_instance = no_args_void_type()
        self.assertEqual(
            type(no_args_void_instance),
            no_args_void_type,
        )
        self.assertTrue(
            isinstance(no_args_void_instance, FunctionBase),
            "no_args_void_instance inherits FunctionBase",
        )
