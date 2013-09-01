"""
A collection of utilities to help in writing tests for the compiler framework.

The stuff in here shouldn't be used anywhere in the framework code itself.
It may only be used from the unit tests.
"""

import alamatic.ast
import alamatic.types
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


def generate_c_code_for_tree(root):
    """
    Given the root node of a codegen tree or subtree thereof (but _not_
    a parse tree), returns the C code generated by it as a string.

    If any errors are generated during code generation, raises a
    :py:class:`OperationGeneratedErrors` and emits the errors via the
    standard Python :py:mod:`logging` mechanism.
    """
    from alamatic.compiler import CompileState
    from alamatic.codegen import CodeWriter
    from alamatic.compilelogging import LoggingCompileLogHandler
    from StringIO import StringIO
    state = CompileState(log_handler=LoggingCompileLogHandler())
    stream = StringIO()
    writer = CodeWriter(stream)
    root.generate_c_code(state, writer)
    if state.error_count > 0:
        raise OperationGeneratedErrors(
            "Errors during Code Generation (see logging)"
        )
    return stream.getvalue()


def get_scope_values(symbols, data):
    """
    Given a symbol table and a data state, return a dictionary of symbol
    names mapping to values, thus flattening all of the indirection
    via the data state.

    This provides a snapshot of the given symbol table, but it only
    works on the symbols directly in the symbol table. Any objects inside
    that have their own symbols will not be resolved automatically.
    """
    from interpreter import SymbolValueNotKnownError
    ret = {}
    for name in symbols.all_names:
        symbol = symbols.get_symbol(name)
        try:
            ret[name] = data.get_symbol_value(symbol)
        except SymbolValueNotKnownError:
            ret[name] = None
    return ret


def execute_stmts(stmts, global_data={}):
    """
    Given either a statement or a :py:class:`list` of statements,
    execute them in the interpreter and return an object with
    `global_data` and `runtime_stmts` members, where the former is the
    contents of the global scope after completion and the latter
    is the list of statements that would need to be fed into the code
    generator, if any.

    This function does not suppress any exceptions raised by the
    interpreter during runtime. If any statement returns successfully
    but generates errors in the log, raises
    :py:class`OperationGeneratedErrors`.
    """
    if type(stmts) not in (tuple, list):
        stmts = (stmts,)

    from alamatic.compiler import CompileState
    from alamatic.interpreter import interpreter, SymbolTable, DataState
    from alamatic.compilelogging import LoggingCompileLogHandler
    old_state = interpreter.state
    interpreter.state = CompileState(log_handler=LoggingCompileLogHandler())

    class ExecuteStmtsReturn(object):
        pass

    try:
        with SymbolTable() as root_symbols:
            with DataState() as root_data:
                for name, value in global_data.iteritems():
                    interpreter.declare_and_init(name, value)

                runtime_stmts = []
                for stmt in stmts:
                    stmt.execute(runtime_stmts)

                    if interpreter.state.error_count > 0:
                        raise OperationGeneratedErrors(
                            "Errors during execution (see logging)"
                        )

                ret = ExecuteStmtsReturn()
                ret.runtime_stmts = runtime_stmts
                ret.global_data = get_scope_values(
                    root_symbols,
                    root_data,
                )
                root_data.finalize_values()
                return ret
    finally:
        interpreter.state = old_state


class DummyStmtCompileTime(alamatic.ast.Statement):
    def __init__(self, sigil):
        self.sigil = sigil
        self.executed = False

    @property
    def params(self):
        yield self.sigil

    def execute(self, runtime_stmts):
        # Does nothing and generates no statements,
        # so should be absent in a codegen tree.
        self.executed = True


class DummyStmtRuntime(alamatic.ast.Statement):
    def __init__(self, sigil):
        self.sigil = sigil
        self.executed = False

    @property
    def params(self):
        yield self.sigil

    def execute(self, runtime_stmts):
        # Unconditionally produces a copy of itself in the codegen tree.
        runtime_stmts.append(
            DummyStmtRuntime(self.sigil),
        )
        self.executed = True

    def generate_c_code(self, state, writer):
        writer.writeln(
            "// DUMMY %s" % str(self.sigil)
        )


def DummyStatementBlock(stmts):
    from alamatic.interpreter import SymbolTable
    from alamatic.ast import StatementBlock
    return StatementBlock(
        stmts,
        SymbolTable(),
    )


class DummyAssignStmt(alamatic.ast.Statement):
    def __init__(self, name, value):
        self.name = name
        self.value = value
        self.executed = False

    @property
    def params(self):
        yield self.name
        yield self.value

    def execute(self, runtime_stmts):
        from alamatic.interpreter import interpreter
        if self.value is not None:
            interpreter.assign(self.name, self.value)
        else:
            interpreter.mark_unknown(self.name)
        self.executed = True

    def find_assigned_symbols(self):
        from alamatic.interpreter import interpreter
        yield interpreter.get_symbol(self.name)


class DummyIncrementStmt(alamatic.ast.Statement):
    def __init__(self, name, amount=1):
        self.name = name
        self.amount = amount
        self.executed = False

    @property
    def params(self):
        yield self.name
        yield self.amount

    def execute(self, runtime_stmts):
        self.executed = True
        from alamatic.interpreter import interpreter
        if interpreter.value_is_known(self.name):
            old_value = interpreter.retrieve(self.name)
            if isinstance(old_value, DummyType):
                new_value = DummyType(old_value.value + self.amount)
                interpreter.assign(self.name, new_value)
            else:
                raise Exception(
                    "DummyIncrementStmt can only increment DummyType values"
                    " but this one was given %r" % old_value
                )
        else:
            interpreter.mark_symbol_used_at_runtime(
                interpreter.get_symbol(self.name),
                self.position,
            )
            runtime_stmts.append(
                DummyIncrementStmt(
                    self.name,
                    self.amount,
                )
            )

    def find_assigned_symbols(self):
        from alamatic.interpreter import interpreter
        yield interpreter.get_symbol(self.name)

    def generate_c_code(self, state, writer):
        writer.writeln("DUMMY(%s+=%i);" % (self.name, self.amount))


class DummyDataDeclStmt(alamatic.ast.Statement):
    def __init__(self, name, value):
        self.name = name
        self.value = value
        self.executed = False

    @property
    def params(self):
        yield self.name
        yield self.value

    def execute(self, runtime_stmts):
        from alamatic.interpreter import interpreter
        interpreter.declare_and_init(self.name, self.value)
        self.executed = True


class DummyType(alamatic.types.Value):
    from weakref import WeakValueDictionary
    instances = WeakValueDictionary()

    def __new__(cls, value):
        if value not in cls.instances:
            self = object.__new__(cls)
            self.value = value
            cls.instances[value] = self
        return cls.instances[value]

    def __repr__(self):
        return "<alamatic.testutil.%s: %r>" % (
            type(self).__name__,
            self.value,
        )

    def auto_op_method(f):
        @functools.wraps(f)
        def op_method(*args, **kwargs):
            return alamatic.ast.ValueExpr(
                alamatic.ast.DummyType(
                    f(*args, **kwargs)
                )
            )
        return op_method

    def auto_binop_method(f):
        @functools.wraps(f)
        def op_method(source_node, lhs, rhs, *args, **kwargs):
            return alamatic.ast.ValueExpr(
                alamatic.ast.DummyType(
                    f(lhs.value, rhs.value, *args, **kwargs)
                )
            )
        return op_method

    @auto_binop_method
    def add(self, lhs, rhs):
        return lhs + rhs

    @auto_binop_method
    def equals(self, lhs, rhs):
        return lhs == rhs

    def __eq__(self, other):
        if type(other) is type(self):
            return self.value == other.value
        else:
            return False

    @classmethod
    def c_type_spec(self):
        return "DummyType"


class DummyExprCompileTime(alamatic.ast.Expression):
    def __init__(self, sigil, value=DummyType(None)):
        self.sigil = sigil
        self.value = value
        self.evaluated = False

    @property
    def params(self):
        yield self.sigil

    def evaluate(self):
        self.evaluated = True
        return alamatic.ast.ValueExpr(
            None,
            self.value,
        )


class DummyExprRuntime(alamatic.ast.Expression):
    def __init__(self, sigil, result_type=DummyType):
        self.sigil = sigil
        self.evaluated = False
        self._result_type = result_type

    @property
    def params(self):
        yield self.sigil
        yield self._result_type

    def evaluate(self):
        self.evaluated = True
        return DummyExprRuntime(
            self.sigil,
            self._result_type,
        )

    def generate_c_code(self, state, writer):
        writer.write("DUMMY(%s)" % str(self.sigil))

    @property
    def result_type(self):
        return self._result_type


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

    def assign(self, expr):
        return DummyExprLvalue(
            self.sigil,
            expr,
        )

    def generate_c_code(self, state, writer):
        writer.write("DUMMY(%s)" % str(self.sigil))


class DummyBooleanConstantExpr(alamatic.ast.Expression):
    def __init__(self, value):
        from alamatic.types import Bool
        self.ret = alamatic.ast.ValueExpr(
            None,
            Bool(value)
        )

    @property
    def params(self):
        yield self.ret.value.value

    def evaluate(self):
        return self.ret


class DummyLessThanTestExpr(alamatic.ast.Expression):
    def __init__(self, name, limit):
        self.name = name
        self.limit = limit
        self.evaluated = False

    @property
    def params(self):
        yield self.name
        yield self.limit

    def evaluate(self):
        self.evaluated = True
        from alamatic.interpreter import interpreter
        from alamatic.types import Bool

        if interpreter.value_is_known(self.name):
            value = interpreter.retrieve(self.name)
            if isinstance(value, DummyType):
                return alamatic.ast.ValueExpr(
                    None,
                    Bool(value.value < self.limit),
                )
            else:
                raise Exception(
                    "DummyLessThanTestExpr can only test DummyType values"
                    " but this one was given %r" % value
                )
        else:
            interpreter.mark_symbol_used_at_runtime(
                interpreter.get_symbol(self.name),
                self.position,
            )
            return DummyLessThanTestExpr(
                self.name,
                self.limit,
            )

    @property
    def result_type(self):
        from alamatic.types import Bool
        return Bool

    def generate_c_code(self, state, writer):
        writer.write("DUMMY(%s<%i)" % (self.name, self.limit))


# These testcase_-prefixed functions are intended to be added to
# TestCase subclasses as needed,
def testcase_assertCodegenTree(testcase, stmts, expected):
    result = execute_stmts(stmts)
    testcase.assertEqual(
        ast_comparison_nodes(result.runtime_stmts),
        expected,
    )
testcase_assertCodegenTree.__name__ = "assertCodegenTree"


def testcase_assertDataResult(testcase, initial_data, stmts, expected_data):
    result = execute_stmts(stmts, initial_data)
    testcase.assertEqual(
        result.global_data,
        expected_data,
    )
testcase_assertDataResult.__name__ = "assertDataResult"


def testcase_assertCCode(testcase, node, expected_code):
    got_code = generate_c_code_for_tree(node)
    testcase.assertEqual(
        got_code,
        expected_code,
    )
testcase_assertCCode.__name__ = "assertCCode"


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


class LanguageTestCase(unittest.TestCase):
    assertCodegenTree = testcase_assertCodegenTree
    assertDataResult = testcase_assertDataResult
    assertCCode = testcase_assertCCode
    assertStmtParseTree = testcase_assertStmtParseTree
    assertExprParseTree = testcase_assertExprParseTree
    assertErrorsInStmts = testcase_assertErrorsInStmts
    assertErrorsInExpr = testcase_assertErrorsInExpr
