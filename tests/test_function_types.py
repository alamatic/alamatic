
from alamatic.ast import *
from alamatic.types import *
from alamatic.testutil import *
from mock import MagicMock


class TestFunctionType(LanguageTestCase):

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


class TestFunctionTemplateType(LanguageTestCase):

    def test_correct_arg_count(self):
        from alamatic.interpreter import InvalidParameterListError

        stmt = MagicMock(name='stmt')
        decl = MagicMock(name='decl')
        scope = MagicMock(name='scope')
        param_decls = []

        stmt.decl = decl
        decl.param_decls = param_decls

        stmt.position = ('test.ala', 1, 0)

        template = FunctionTemplate(stmt, scope)

        args = MagicMock(name='args')
        args.exprs = []

        try:
            template._assert_correct_args(args)
        except InvalidParameterListError:
            self.fail("Unexpected InvalidParameterListError")

        args.exprs = [MagicMock(name='arg_expr')]

        self.assertRaises(
            InvalidParameterListError,
            lambda: template._assert_correct_args(args)
        )

        param_decls.append(MagicMock(name='param_decl'))

        try:
            template._assert_correct_args(args)
        except InvalidParameterListError:
            self.fail("Unexpected InvalidParameterListError")

        args.exprs = []
        self.assertRaises(
            InvalidParameterListError,
            lambda: template._assert_correct_args(args)
        )

        try:
            template._assert_correct_args(args, position=('test.ala', 2, 0))
        except InvalidParameterListError, ex:
            positions_mentioned = ex.log_line.positions_mentioned
            self.assertTrue(
                ('test.ala', 1, 0) in positions_mentioned,
            )
            self.assertTrue(
                ('test.ala', 2, 0) in positions_mentioned,
            )
            self.assertEqual(
                len(positions_mentioned),
                2,
            )
        else:
            self.fail("Expected InvalidParameterListError")
