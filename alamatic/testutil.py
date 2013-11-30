"""
A collection of utilities to help in writing tests for the compiler framework.

The stuff in here shouldn't be used anywhere in the framework code itself.
It may only be used from the unit tests.
"""

import alamatic.ast
import alamatic.types
import alamatic.intermediate
import alamatic.analyser
import functools
import unittest


class OperationGeneratedErrors(Exception):
    pass


def ast_comparison_nodes(nodes):
    ret = []
    for node in nodes:
        ret.append(ast_comparison_node(node))
    return ret


def ast_comparison_node(node):
    if node is None:
        return None
    return (
        type(node).__name__,
        tuple(node.params),
        ast_comparison_nodes(node.child_nodes),
    )


def element_comparison_nodes(elements):
    ret = []
    for element in elements:
        ret.append(element_comparison_node(element))
    return ret


def element_comparison_node(element):
    if element is None:
        return None
    return (
        type(element).__name__,
        element_param_comparison_nodes(element.params),
    )


def element_param_comparison_nodes(params):
    ret = []
    for param in params:
        ret.append(element_param_comparison_node(param))
    return ret


def element_param_comparison_node(param):
    if isinstance(param, alamatic.intermediate.Operand):
        return (type(param).__name__, tuple(param.params))
    elif isinstance(param, alamatic.intermediate.Label):
        return (type(param).__name__,)
    else:
        return param


def parse_stmts(inp):
    from alamatic.parser import parse_module
    caller = inspect.stack()[1]
    state = CompileState()
    module = parse_module(
        state,
        StringIO(inp),
        caller[3],
        "%s:%i" % (caller[3], caller[2]),
    )
    return module.stmts


class DummyStmt(alamatic.ast.Statement):
    def __init__(self, sigil):
        self.sigil = sigil

    @property
    def params(self):
        yield self.sigil


def DummyStatementBlock(stmts):
    from alamatic.interpreter import SymbolTable
    from alamatic.ast import StatementBlock
    return StatementBlock(
        stmts,
        SymbolTable(),
    )


class DummyType(alamatic.types.Value):
    from weakref import WeakValueDictionary
    instances = WeakValueDictionary()

    def __new__(cls, value):
        instance_key = (type(value), value)
        if instance_key not in cls.instances:
            self = object.__new__(cls)
            self.value = value
            cls.instances[instance_key] = self
        return cls.instances[instance_key]

    def __repr__(self):
        return "<alamatic.testutil.%s: %r>" % (
            type(self).__name__,
            self.value,
        )

    def auto_op_method(f):
        @classmethod
        @functools.wraps(f)
        def op_method(*args, **kwargs):
            return alamatic.ast.ValueExpr(
                alamatic.ast.DummyType(
                    f(*args, **kwargs)
                )
            )
        return op_method

    def auto_binop_method(f):
        @classmethod
        @functools.wraps(f)
        def op_method(source_node, lhs, rhs, *args, **kwargs):
            return alamatic.ast.ValueExpr(
                alamatic.ast.DummyType(
                    f(lhs.value, rhs.value, *args, **kwargs)
                )
            )
        return op_method

    @auto_binop_method
    def add(self, lhs, rhs, position=None):
        return lhs + rhs

    @auto_binop_method
    def equals(self, lhs, rhs, position=None):
        return lhs == rhs

    def __eq__(self, other):
        if type(other) is type(self):
            return self.value == other.value
        else:
            return False

    @classmethod
    def c_type_spec(self):
        return "DummyType"


class DummyExpr(alamatic.ast.Expression):
    def __init__(self, sigil):
        self.sigil = sigil

    @property
    def params(self):
        yield self.sigil

    def make_intermediate_form(self, elems, symbols):
        elems.append(DummyOperation(self.sigil))
        return DummyOperand(self.sigil)


class DummyExprLvalue(alamatic.ast.Expression):
    def __init__(self, sigil, assigned_expr=None):
        self.sigil = sigil
        self.assigned_expr = assigned_expr

    @property
    def params(self):
        yield self.sigil

    @property
    def child_nodes(self):
        if self.assigned_expr is not None:
            yield self.assigned_expr

    def get_lvalue_operand(self, elems, symbols):
        elems.append(DummyOperation(self.sigil))
        return DummyOperand(self.sigil)


class DummyBooleanConstantExpr(alamatic.ast.Expression):
    def __init__(self, value):
        from alamatic.types import Bool
        self.operand = alamatic.intermediate.ConstantOperand(
            Bool(value)
        )

    @property
    def params(self):
        yield self.ret.value.value

    def make_intermediate_form(self, elems, symbols):
        return self.operand


class DummyOperation(alamatic.intermediate.Operation):
    def __init__(self, sigil):
        self.sigil = sigil

    @property
    def params(self):
        yield self.sigil


class DummyOperandDeclOperation(alamatic.intermediate.Operation):
    def __init__(self, sigil):
        self.sigil = sigil
        self.operand = DummyOperand(sigil)

    @property
    def params(self):
        yield self.operand


class DummyOperand(alamatic.intermediate.Operand):
    def __init__(self, sigil):
        self.sigil = sigil

    @property
    def params(self):
        yield self.sigil


# These testcase_-prefixed functions are intended to be added to
# TestCase subclasses as needed,
def testcase_assertCodegenTree(testcase, stmts, expected):
    result = execute_stmts(stmts)
    testcase.assertEqual(
        ast_comparison_nodes(result.runtime_stmts),
        expected,
    )
testcase_assertCodegenTree.__name__ = "assertCodegenTree"


def testcase_assertStmtParseTree(testcase, inp, expected):
    from alamatic.parser import parse_module
    from alamatic.compiler import CompileState
    from alamatic.compilelogging import LoggingCompileLogHandler
    import inspect
    from StringIO import StringIO

    caller = inspect.stack()[1]
    log_handler = LoggingCompileLogHandler()
    state = CompileState(log_handler=log_handler)
    module = parse_module(
        state,
        StringIO(inp),
        caller[3],
        "%s:%i" % (caller[3], caller[2]),
    )
    got = ast_comparison_nodes(module.block.stmts)
    testcase.assertTrue(state.error_count == 0, "Errors during parse")
    testcase.assertEqual(got, expected)
testcase_assertStmtParseTree.__name__ = "assertParseTree"


def testcase_assertExprParseTree(testcase, inp, expected, allow_assign=False):
    from alamatic.parser import parse_expression
    from alamatic.compiler import CompileState
    from alamatic.compilelogging import LoggingCompileLogHandler
    import inspect
    from StringIO import StringIO

    caller = inspect.stack()[1]
    log_handler = LoggingCompileLogHandler()
    state = CompileState(log_handler=log_handler)
    expr = parse_expression(
        state,
        StringIO(inp),
        "%s:%i" % (caller[3], caller[2]),
        allow_assign=allow_assign
    )
    got = ast_comparison_node(expr)
    testcase.assertTrue(
        state.error_count == 0,
        "Errors during parse (see error log)",
    )
    testcase.assertEqual(got, expected)
testcase_assertExprParseTree.__name__ = "assertExprParseTree"


def testcase_assertErrorsInStmts(testcase, inp, positions):
    from alamatic.parser import parse_module
    from alamatic.compilelogging import (
        InMemoryCompileLogHandler,
        LoggingCompileLogHandler,
        MultiCompileLogHandler,
        ERROR,
    )
    from alamatic.compiler import CompileState
    import inspect
    from StringIO import StringIO

    caller = inspect.stack()[1]
    in_memory_log_handler = InMemoryCompileLogHandler()
    logging_log_handler = LoggingCompileLogHandler()
    log_handler = MultiCompileLogHandler((
        in_memory_log_handler,
        logging_log_handler,
    ))
    state = CompileState(log_handler=log_handler)
    module = parse_module(
        state,
        StringIO(inp),
        caller[3],
        "%s:%i" % (caller[3], caller[2]),
    )
    got_positions = []
    for line in in_memory_log_handler.lines:
        if line.level == ERROR:
            for position in line.positions_mentioned:
                got_positions.append((position[1], position[2]))

    testcase.assertEqual(got_positions, positions)
testcase_assertErrorsInStmts.__name__ = "assertErrorsInStmts"


def testcase_assertErrorsInExpr(self, inp, positions, allow_assign=False):
    from alamatic.parser import parse_expression
    from alamatic.compilelogging import (
        InMemoryCompileLogHandler,
        LoggingCompileLogHandler,
        MultiCompileLogHandler,
        ERROR,
    )
    from alamatic.compiler import CompileState
    import inspect
    from StringIO import StringIO

    caller = inspect.stack()[1]
    in_memory_log_handler = InMemoryCompileLogHandler()
    logging_log_handler = LoggingCompileLogHandler()
    log_handler = MultiCompileLogHandler((
        in_memory_log_handler,
        logging_log_handler,
    ))
    state = CompileState(log_handler=log_handler)
    expr = parse_expression(
        state,
        StringIO(inp),
        "%s:%i" % (caller[3], caller[2]),
        allow_assign=allow_assign,
    )
    got_positions = []
    for line in in_memory_log_handler.lines:
        if line.level == ERROR:
            for position in line.positions_mentioned:
                got_positions.append((position[1], position[2]))

    self.assertEqual(got_positions, positions)
testcase_assertErrorsInExpr.__name__ = "assertErrorsInExpr"


def testcase_assertIntermediateForm(
    self, inp, expected_elems, expected_target=None, init_symbols=None,
):
    elems = []
    symbols = alamatic.intermediate.SymbolTable()
    if init_symbols is not None:
        for symbol_name in init_symbols:
            symbols.declare(symbol_name)
    result = inp.make_intermediate_form(elems, symbols)
    self.assertEqual(
        element_comparison_nodes(elems),
        expected_elems,
    )
    if expected_target is not None:
        self.assertEqual(
            element_param_comparison_node(result),
            expected_target,
        )
    else:
        self.assertEqual(
            result,
            None,
        )
testcase_assertIntermediateForm.__name__ = "assertIntermediateForm"


class LanguageTestCase(unittest.TestCase):
    assertCodegenTree = testcase_assertCodegenTree
    assertStmtParseTree = testcase_assertStmtParseTree
    assertExprParseTree = testcase_assertExprParseTree
    assertErrorsInStmts = testcase_assertErrorsInStmts
    assertErrorsInExpr = testcase_assertErrorsInExpr
    assertIntermediateForm = testcase_assertIntermediateForm
