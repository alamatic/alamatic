
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

    def test_abstract_base(self):
        self.assertRaises(
            Exception,
            lambda: FunctionBase()
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

    def test_call_unknown_template(self):
        from alamatic.interpreter import (
            interpreter,
            NotConstantError,
        )

        expr = DummyExprRuntime('callee')
        arg_exprs = MagicMock()
        arg_exprs.exprs = []

        self.assertRaises(
            NotConstantError,
            lambda: FunctionTemplate.call(
                expr,
                arg_exprs,
            )
        )

    def test_call_not_pure_function(self):
        from alamatic.interpreter import (
            interpreter,
            DataState,
            NotConstantError,
        )

        position = ('foo.ala', 6, 0)

        mock_function = MagicMock('function')
        mock_function.args_type = MagicMock('args_type')
        mock_function.args_type.return_value = DummyType(1)

        mock_template = MagicMock('template')
        mock_template.constant_call = MagicMock()
        mock_template.constant_call.side_effect = NotConstantError('')
        mock_template._assert_correct_args = MagicMock()
        mock_template._assert_correct_args.return_value = None
        mock_template.instantiate = MagicMock()
        mock_template.instantiate.return_value = mock_function

        expr = DummyExprCompileTime('expr', mock_template)

        args = ExpressionList([
            DummyExprCompileTime('arg1'),
            DummyExprCompileTime('arg2'),
        ])

        with DataState():
            result = FunctionTemplate.call(
                expr,
                args,
                position=position,
            )

        self.assertEqual(
            type(result),
            RuntimeFunctionCallExpr,
        )
        self.assertEqual(
            result.position,
            ('foo.ala', 6, 0),
        )
        self.assertEqual(
            result.function,
            mock_function,
        )
        self.assertEqual(
            type(result.args),
            DummyType,
        )
        self.assertEqual(
            result.args.value,
            1,
        )

        mock_template.constant_call.assert_called_with(
            args,
            position=position,
        )
        mock_template.instantiate.assert_called_with(
            [DummyType, DummyType],
            call_position=position,
        )
        mock_function.args_type.assert_called_with(args)

    def test_call_constant_void(self):
        from alamatic.interpreter import (
            interpreter,
            DataState,
            NotConstantError,
        )

        position = ('foo.ala', 8, 0)

        mock_template = MagicMock('template')
        mock_template.constant_call = MagicMock()
        mock_template.constant_call.return_value = None

        expr = DummyExprCompileTime('expr', mock_template)

        args = ExpressionList([
            DummyExprCompileTime('arg1'),
            DummyExprCompileTime('arg2'),
        ])

        data = DataState()
        data.merge_children = MagicMock('merge_children')

        with data:
            result = FunctionTemplate.call(
                expr,
                args,
                position=position,
            )

        self.assertEqual(
            type(result),
            VoidExpr,
        )
        self.assertEqual(
            result.position,
            position,
        )
        self.assertTrue(
            data.merge_children.called
        )
        mock_template.constant_call.assert_called_with(
            args,
            position=position,
        )

    def test_call_constant_not_void(self):
        from alamatic.interpreter import (
            interpreter,
            DataState,
            NotConstantError,
        )

        position = ('foo.ala', 8, 0)

        mock_template = MagicMock('template')
        mock_template.constant_call = MagicMock()
        mock_template.constant_call.return_value = DummyType(2)

        expr = DummyExprCompileTime('expr', mock_template)

        args = ExpressionList([
            DummyExprCompileTime('arg1'),
            DummyExprCompileTime('arg2'),
        ])

        data = DataState()
        data.merge_children = MagicMock('merge_children')

        with data:
            result = FunctionTemplate.call(
                expr,
                args,
                position=position,
            )

        self.assertEqual(
            type(result),
            ValueExpr,
        )
        self.assertEqual(
            type(result.value),
            DummyType,
        )
        self.assertEqual(
            result.value.value,
            2,
        )
        self.assertEqual(
            result.position,
            position,
        )
        self.assertTrue(
            data.merge_children.called
        )
        mock_template.constant_call.assert_called_with(
            args,
            position=position,
        )

    def test_instantiate(self):
        from alamatic.interpreter import (
            SymbolTable,
            DataState,
            CallFrame,
            RuntimeFunction,
            InvalidParameterListError,
        )

        decl_stmt = FuncDeclStmt(
            ('decl_stmt', 1, 0),
            FuncDeclClause(
                ('decl', 1, 0),
                'foo',
                [
                    ParamDeclClause(
                        ('param1', 1, 0),
                        'param1',
                        None,
                    ),
                    ParamDeclClause(
                        ('param2', 1, 0),
                        'param2',
                        None,
                    ),
                ]
            ),
            DummyStatementBlock([
                DummyStmtRuntime('body_runtime'),
                DummyStmtCompileTime('body_compiletime'),
                # To test that param1 and param2 aren't known at compile time
                ExpressionStmt(
                    None,
                    DummyLessThanTestExpr('param1', 0),
                ),
                ExpressionStmt(
                    None,
                    DummyLessThanTestExpr('param2', 0),
                )
            ])
        )

        parent_scope = SymbolTable()
        root_data = DataState()
        root_frame = CallFrame()

        template = FunctionTemplate(decl_stmt, parent_scope)

        with root_data:
            with root_frame:
                dummy_dummy_result = template.instantiate(
                    (DummyType, DummyType),
                    ('call', 1, 0),
                )

        self.assertEqual(
            type(dummy_dummy_result),
            RuntimeFunction,
        )
        self.assertEqual(
            dummy_dummy_result.decl_position,
            ('decl_stmt', 1, 0),
        )
        self.assertEqual(
            ast_comparison_node(dummy_dummy_result.runtime_block),
            ('StatementBlock', (), [
                ('DummyStmtRuntime', ('body_runtime',), []),
                # These are still here because param1 and param2 are treated
                # as not being known at compile time.
                ('ExpressionStmt', (), [
                    ('DummyLessThanTestExpr', ('param1', 0), []),
                ]),
                ('ExpressionStmt', (), [
                    ('DummyLessThanTestExpr', ('param2', 0), []),
                ]),
            ]),
        )
        self.assertEqual(
            [x.decl_name for x in dummy_dummy_result.args_type.param_symbols],
            ['param1', 'param2'],
        )
        self.assertEqual(
            dummy_dummy_result.return_type,
            Void,
        )

        with root_data:
            with root_frame:
                self.assertRaises(
                    InvalidParameterListError,
                    lambda: template.instantiate(
                        (DummyType,),
                        ('call', 1, 0),
                    )
                )
                self.assertRaises(
                    InvalidParameterListError,
                    lambda: template.instantiate(
                        (DummyType, DummyType, DummyType),
                        ('call', 1, 0),
                    )
                )

        # Test that if we instantiate again with the same key
        # we get back the same instance.
        with root_data:
            with root_frame:
                dummy_dummy_result_2 = template.instantiate(
                    (DummyType, DummyType),
                    ('call', 1, 0),
                )
        self.assertTrue(
            dummy_dummy_result_2 is dummy_dummy_result
        )

        # But different key gets a different instance.
        with root_data:
            with root_frame:
                int32_dummy_result = template.instantiate(
                    (Int32, DummyType),
                    ('call', 1, 0),
                )
        self.assertTrue(
            int32_dummy_result is not dummy_dummy_result
        )
