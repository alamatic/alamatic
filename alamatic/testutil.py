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
    # Assign indices to any labels we see so we've some way to
    # identify them in tests.
    label_index = 0
    for element in elements:
        if isinstance(element, alamatic.intermediate.Label):
            element._test_index = label_index
            label_index += 1
    ret = []
    for element in elements:
        if isinstance(element, alamatic.intermediate.Label):
            # this function happens to already have a sensible implementation
            # for labels so we'll just reuse it.
            ret.append(element_param_comparison_node(element))
        else:
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
    from alamatic.types import Value
    if isinstance(param, alamatic.intermediate.Operand):
        return (type(param).__name__, list(
            element_param_comparison_node(x) for x in param.params
        ))
    elif isinstance(param, alamatic.intermediate.Operation):
        return (type(param).__name__, list(
            element_param_comparison_node(x) for x in param.params
        ))
    elif isinstance(param, alamatic.intermediate.Label):
        return (type(param).__name__, getattr(param, "_test_index", None))
    elif isinstance(param, alamatic.intermediate.TemporarySymbol):
        return (type(param).__name__, param.index)
    elif isinstance(param, alamatic.intermediate.NamedSymbol):
        return (type(param).__name__, param.decl_name)
    elif isinstance(param, Value):
        return (type(param).__name__, tuple(param.params))
    elif isinstance(param, list):
        return [
            element_param_comparison_node(x) for x in param
        ]
    elif isinstance(param, dict):
        return {
            k: element_param_comparison_node(v)
            for k, v in param.iteritems()
        }
    else:
        return param


def control_flow_graph_comparison_node(graph):
    from alamatic.analyser import ControlFlowGraph

    # Allow the caller to pass either a graph or just a bare list of blocks
    if isinstance(graph, ControlFlowGraph):
        blocks = graph.blocks
    else:
        blocks = graph

    ret = []
    block_indices = {}
    for i, block in enumerate(blocks):
        item = []
        item.append(element_comparison_node(block.label))
        item.append(element_comparison_nodes(block.operations))
        item.append(element_comparison_node(block.terminator))
        item.append(block.successors)
        block_indices[block] = i
        ret.append(item)

    # The tests using this function won't have the actual block instances
    # handy to compare to, so we substutute indices instead.
    for item in ret:
        item[3] = tuple(sorted(
            block_indices[b] for b in item[3]
        ))

    return ret


# Entry block always looks the same: no operations, falls through to index 1
entry_block_comparison_node = [
    None,
    [],
    ('JumpNeverInstruction', []),
    (1,),
]


# Exit block always looks the same: no operations, no successors
exit_block_comparison_node = [
    None,
    [],
    ('JumpNeverInstruction', []),
    (),
]


def dominator_tree_comparison_node(graph):
    ret = []
    for block in graph.blocks:
        item = [
            x.index
            for x in sorted(block.dominators, key=lambda b: b.index)
        ]
        ret.append(item)
    return ret


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

    def make_intermediate_form(self, elems, symbols):
        elems.append(DummyInstruction(self.sigil))


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
        elems.append(DummyInstruction(self.sigil))
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
        elems.append(DummyInstruction(self.sigil))
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


class DummyBasicBlock(object):
    from alamatic.analyser import BasicBlock

    def __init__(self, cfg):
        self.cfg = cfg
        self.successors = set()
        self.predecessors = set()
        self.dominators = set()
        self.index = None

    def __repr__(self):
        return "<DummyBasicBlock %r>" % self.index

    # Borrow the is_loop_header implementation from BasicBlock,
    # or else we'd just duplicate it here anyway.
    is_loop_header = BasicBlock.is_loop_header

    @classmethod
    def create_list(cls, *jump_defs):
        from mock import MagicMock

        mock_cfg = MagicMock()

        blocks = [
            DummyBasicBlock(mock_cfg) for x in jump_defs
        ]
        for i, jump_def in enumerate(jump_defs):
            blocks[i].index = i
            blocks[i].successors.update(
                blocks[bi] for bi in jump_def
            )
            for successor_block in blocks[i].successors:
                successor_block.predecessors.add(blocks[i])

        # Assume the first block passed was the entry block.
        # An entry block is required to build the dominator map.
        mock_cfg.entry_block = blocks[0]

        # And we build the dominators map using our real analyzer function,
        # since otherwise we'd just repeat the whole thing here.
        from alamatic.analyser import _create_dominator_map_for_blocks
        dominator_map = _create_dominator_map_for_blocks(blocks)
        for block, dominators in dominator_map.iteritems():
            block.dominators.update(dominators)

        return blocks


class DummyInstruction(alamatic.intermediate.Instruction):
    def __init__(self, sigil):
        self.sigil = sigil

    @property
    def params(self):
        yield self.sigil


class DummyOperandDeclInstruction(alamatic.intermediate.Instruction):
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

    def generate_c_code(self, state, writer):
        writer.write("DUMMY(%s)" % self.sigil)


def binary_expr_operator_map_case_func(expr_type, ast_op, int_op):
    def test_impl(self):
        expr = expr_type(
            None,
            DummyExpr("lhs"),
            ast_op,
            DummyExpr("rhs"),
        )
        self.assertEqual(
            expr.operator_name,
            int_op,
        )
    test_impl.__name__ = "test_" + int_op
    return test_impl


def binary_expr_operator_map_case(expr_type, operations):
    cls_dict = {}
    for ast_op, int_op in operations.iteritems():
        cls_dict["test_" + int_op] = binary_expr_operator_map_case_func(
            expr_type,
            ast_op,
            int_op,
        )
    return type('TestOperatorMap', (LanguageTestCase,), cls_dict)


def generate_c_for_elems(elems):
    from StringIO import StringIO
    from alamatic.compiler import CompileState
    from alamatic.codegen import CodeWriter
    state = CompileState()
    f = StringIO()
    writer = CodeWriter(f)
    for elem in elems:
        elem.generate_c_code(state, writer)
    return f.getvalue()


def generate_c_for_instruction(op):
    from StringIO import StringIO
    from alamatic.compiler import CompileState
    from alamatic.codegen import CodeWriter
    state = CompileState()
    f = StringIO()
    writer = CodeWriter(f)
    op._generate_c_code(state, writer)
    return f.getvalue()


def generate_c_for_operation(op):
    from StringIO import StringIO
    from alamatic.compiler import CompileState
    from alamatic.codegen import CodeWriter
    state = CompileState()
    f = StringIO()
    writer = CodeWriter(f)
    op.generate_c_code(state, writer)
    return f.getvalue()


def get_operation_replaceable_operands(oper):
    replaced = set()

    def replace(operand):
        replaced.add(operand)
        return operand

    oper.replace_operands(replace)
    return replaced


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
    self, inp, expected_elems, expected_target=None, symbols=None,
):
    elems = []
    if symbols is None:
        symbols = alamatic.intermediate.SymbolTable()
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


def testcase_assertControlFlowGraph(
    self, elems, expected,
):
    graph = alamatic.analyser.build_control_flow_graph(elems)
    self.assertEqual(
        control_flow_graph_comparison_node(graph),
        expected,
    )
testcase_assertControlFlowGraph.__name__ = "assertControlFlowGraph"


def testcase_assertDominatorTree(
    self, elems, expected,
):
    graph = alamatic.analyser.build_control_flow_graph(elems)
    self.assertEqual(
        dominator_tree_comparison_node(graph),
        expected,
    )
testcase_assertDominatorTree.__name__ = "assertDominatorTree"


class LanguageTestCase(unittest.TestCase):
    assertCodegenTree = testcase_assertCodegenTree
    assertStmtParseTree = testcase_assertStmtParseTree
    assertExprParseTree = testcase_assertExprParseTree
    assertErrorsInStmts = testcase_assertErrorsInStmts
    assertErrorsInExpr = testcase_assertErrorsInExpr
    assertIntermediateForm = testcase_assertIntermediateForm
    assertControlFlowGraph = testcase_assertControlFlowGraph
    assertDominatorTree = testcase_assertDominatorTree
