
from alamatic.ast import *


class Statement(AstNode):

    def execute(self, runtime_stmts):
        raise Exception("execute is not implemented for %r" % self)


class ExpressionStmt(Statement):

    def __init__(self, position, expr):
        self.position = position
        self.expr = expr

    @property
    def child_nodes(self):
        yield self.expr

    def execute(self, runtime_stmts):
        from alamatic.ast import ValueExpr
        eval_expr = self.expr.evaluate()
        if not isinstance(eval_expr, ValueExpr):
            runtime_stmts.append(
                ExpressionStmt(
                    self.position,
                    eval_expr,
                )
            )

    def generate_c_code(self, state, writer):
        self.expr.generate_c_code(state, writer)
        writer.writeln(";")


class PassStmt(Statement):
    pass


class BreakStmt(Statement):
    pass


class ContinueStmt(Statement):
    pass


class ReturnStmt(Statement):

    def __init__(self, position, expr=None):
        self.position = position
        self.expr = expr

    @property
    def child_nodes(self):
        if self.expr is not None:
            yield self.expr


class IfStmt(Statement):

    def __init__(self, position, clauses):
        self.position = position
        self.clauses = clauses

    @property
    def child_nodes(self):
        for clause in self.clauses:
            yield clause

    def execute(self, runtime_stmts):
        from alamatic.ast import ValueExpr
        from alamatic.types import Bool
        from alamatic.interpreter import (
            interpreter,
            IncompatibleTypesError,
            NotConstantError,
        )
        from alamatic.compilelogging import pos_link

        runtime_clauses = []
        clause_datas = []
        have_else_clause = False

        for clause in self.clauses:
            if isinstance(clause, IfClause):
                test_expr = clause.test_expr.evaluate()
                if test_expr.result_type is not Bool:
                    raise IncompatibleTypesError(
                        "Test expression must return Bool, not %s" % (
                            test_expr.result_type.__name__,
                        ),
                        " at ", pos_link(clause.test_expr.position),
                    )
            elif isinstance(clause, ElseClause):
                test_expr = ValueExpr(None, Bool(True))
                have_else_clause = True
            else:
                raise Exception(
                    "Don't know how to use %r as an if statement clause" % (
                        clause,
                    )
                )

            test_result = None
            try:
                test_result = test_expr.constant_value.value
            except NotConstantError:
                # Let the result fall through as None
                pass

            if test_result is False:
                # This clause can never run, so skip it.
                continue
            elif test_result is True and len(runtime_clauses) == 0:
                # This clause will *definitely* run, so
                # just inline its block here.
                runtime_block = clause.block.execute()
                runtime_stmts.append(runtime_block.inlined)
                return
            else:
                data = interpreter.child_data_state()
                with data:
                    runtime_block = clause.block.execute()
                if test_result is True:
                    # If we've already generated some clauses but
                    # we know this one is definitely true, then
                    # this is effectively the else clause because
                    # no further clauses can possibly run.
                    have_else_clause = True
                    runtime_clause = ElseClause(
                        clause.position,
                        runtime_block,
                    )
                else:
                    runtime_clause = IfClause(
                        clause.position,
                        test_expr,
                        runtime_block,
                    )
                runtime_clauses.append(runtime_clause)
                clause_datas.append(data)
                if test_result is True:
                    # No need to visit the rest of the clauses.
                    break

        interpreter.data.merge_children(
            clause_datas,
            or_none=not have_else_clause,
        )

        if len(runtime_clauses) > 0:
            runtime_stmts.append(
                IfStmt(
                    self.position,
                    runtime_clauses,
                )
            )

    def generate_c_code(self, state, writer):
        need_elseif = False

        for clause in self.clauses:
            if isinstance(clause, IfClause):
                if need_elseif:
                    writer.write("else ")
                writer.write("if (")
                clause.test_expr.generate_c_code(state, writer)
                writer.write(")")
                clause.block.generate_c_code(state, writer)
                need_elseif = True
            elif isinstance(clause, ElseClause):
                writer.write("else")
                clause.block.generate_c_code(state, writer)
            else:
                raise Exception(
                    "Don't know how to use %r as an if statement clause" % (
                        clause,
                    )
                )


class IfClause(AstNode):

    def __init__(self, position, test_expr, block):
        self.position = position
        self.test_expr = test_expr
        self.block = block

    @property
    def child_nodes(self):
        yield self.test_expr
        yield self.block


class ElseClause(AstNode):

    def __init__(self, position, block):
        self.position = position
        self.block = block

    @property
    def child_nodes(self):
        yield self.block


class WhileStmt(Statement):

    def __init__(self, position, test_expr, block):
        self.position = position
        self.test_expr = test_expr
        self.block = block

    @property
    def child_nodes(self):
        yield self.test_expr
        yield self.block

    def execute(self, runtime_stmts):
        from alamatic.ast import ValueExpr
        from alamatic.types import Bool
        from alamatic.interpreter import (
            interpreter,
            IncompatibleTypesError,
            NotConstantError,
        )
        from alamatic.compilelogging import pos_link

        test_expr = self.test_expr.evaluate()

        if test_expr.result_type is not Bool:
            raise IncompatibleTypesError(
                "Test expression must return Bool, not %s" % (
                    test_expr.result_type.__name__,
                ),
                " at ", pos_link(clause.test_expr.position),
            )

        while True:
            test_expr = self.test_expr.evaluate()
            if test_expr.result_type is not Bool:
                raise IncompatibleTypesError(
                    "Test expression must return Bool, not %s" % (
                        test_expr.result_type.__name__,
                        ),
                    " at ", pos_link(clause.test_expr.position),
                )

            try:
                test_result = test_expr.constant_value.value
                if test_result is False:
                    # Done iterating
                    break
                elif test_result is True:
                    # This iteration will definitely run, so
                    # just inline its block here.
                    # FIXME: This behaves badly if the test expression
                    # remains constant for many iterations but the
                    # block generates runtime stmts... it effectively
                    # unrolls the loop and may result in much larger
                    # code than we otherwise would've had.
                    # This can be fixed once we have a codegen node type for
                    # C-style for loops, so we can test how many times
                    # we generate the same block and turn it into a for loop
                    # which the C compiler is then free to unroll if it wants.
                    runtime_block = self.block.execute()
                    if len(runtime_block.stmts) > 0:
                        runtime_stmts.append(runtime_block.inlined)
                else:
                    # should never happen
                    raise Exception("boolean expr has non-boolean value")
            except NotConstantError:
                # If we can't evaluate the value expression at compile time
                # anymore, we have no idea how many more iterations the
                # loop will run for. Therefore we analyze what state changes
                # the loop *might* cause, mark each of those targets as
                # being unknown, and then execute the body in *that* context
                # to produce a body that is capable of executing all possible
                # code paths for the remainder of the loop.
                data = interpreter.child_data_state()
                with data:
                    for assigned_symbol in self.find_assigned_symbols():
                        interpreter.mark_symbol_unknown(assigned_symbol)

                    # Now execute the block with all of the above unknown
                    # symbols to produce the runtime block.
                    runtime_block = self.block.execute()

                # Now merge the state that resulted from 'executing' the
                # while loop body, including all of those unknowns.
                interpreter.data.merge_children([data], or_none=True)

                runtime_stmt = WhileStmt(
                    self.position,
                    test_expr,
                    runtime_block,
                )
                runtime_stmts.append(runtime_stmt)
                # We don't know if the body will run at runtime
                interpreter.data.merge_children([data], or_none=True)
                break

    def generate_c_code(self, state, writer):
        writer.write("while (")
        self.test_expr.generate_c_code(state, writer)
        writer.write(")")
        self.block.generate_c_code(state, writer)


class ForStmt(Statement):

    def __init__(self, position, target, source_expr, block):
        # target is either a variable declaration or an lvalue expression
        self.position = position
        self.target = target
        self.source_expr = source_expr
        self.block = block

    @property
    def child_nodes(self):
        yield self.target
        yield self.source_expr
        yield self.block


class DataDeclStmt(Statement):

    def __init__(self, position, decl, expr):
        self.position = position
        self.decl = decl
        self.expr = expr

    @property
    def child_nodes(self):
        yield self.decl
        if self.expr is not None:
            yield self.expr

    def execute(self, runtime_stmts):
        from alamatic.interpreter import (
            interpreter,
            NotConstantError,
        )
        from alamatic.ast import (
            ValueExpr,
            AssignExpr,
            SymbolExpr,
            ConstDeclClause,
        )
        from alamatic.compilelogging import pos_link

        const = type(self.decl) is ConstDeclClause

        if self.expr is None:
            if const:
                raise NotConstantError(
                    "Constant '%s'," % self.decl.name,
                    " declared at ", pos_link(self.position),
                    ", must be assigned an initial value",
                )
            else:
                # Create symbol but leave it uninitialized
                interpreter.declare(
                    self.decl.name,
                    position=self.position,
                )
        else:
            val_expr = self.expr.evaluate()
            initial_value = None

            try:
                initial_value = val_expr.constant_value
            except NotConstantError:
                if const:
                    raise NotConstantError(
                        "Initial value for constant '%s'," % self.decl.name,
                        " declared at ", pos_link(self.position),
                        ", can't be determined at compile time",
                    )

            if initial_value is not None:
                interpreter.declare_and_init(
                    self.decl.name,
                    initial_value,
                    const=const,
                    position=self.position,
                )
            else:
                interpreter.declare(
                    self.decl.name,
                    val_expr.result_type,
                    const=const,
                    position=self.position,
                )

            symbol = interpreter.get_symbol(self.decl.name)

            # The code generator will generate the declaration from the scope,
            # so we just need to assign a value to it in the runtime stmts.
            if not const:
                symbol_expr = SymbolExpr(
                    self,
                    symbol,
                )
                assign_expr = symbol_expr.assign(val_expr)
                assign_stmt = ExpressionStmt(
                    self.position,
                    assign_expr,
                )
                runtime_stmts.append(assign_stmt)


class FuncDeclStmt(Statement):

    def __init__(self, position, decl, block):
        self.position = position
        self.decl = decl
        self.block = block

    @property
    def child_nodes(self):
        yield self.decl
        yield self.block


class InlineStatementBlock(Statement):
    """
    When a block will unconditionally execute at runtime,
    such as if we can determine the outcome of an if statement at
    compile time, this statement is used to glue it into the codegen
    tree.
    """

    def __init__(self, block):
        self.block = block

    @property
    def child_nodes(self):
        yield self.block

    def generate_c_code(self, state, writer):
        self.block.generate_c_code(state, writer)
