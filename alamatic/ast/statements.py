
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

    def execute(self, runtime_stmts):
        return


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
        clause_registries = []
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
                registry = interpreter.child_registry()
                with registry:
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
                clause_registries.append(registry)
                if test_result is True:
                    # No need to visit the rest of the clauses.
                    break

        interpreter.registry.merge_children(
            clause_registries,
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

        # A while loop is evaluated at compile time if and only if:
        # * its test expression remains constant until the loop exits
        # * no iterations generate runtime statements
        # * it doesn't contain 'break' or 'continue' statements in
        #  conditional branches that we can't decide until runtime.
        # If any of these conditions do not hold, we give up and generate
        # the code to execute the loop at runtime.
        generate_at_runtime = False

        # First we attempt to run the loop to completion at compile time
        registry = interpreter.child_registry()
        with registry:
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
                        runtime_block = self.block.execute()
                        if len(runtime_block.stmts) > 0:
                            # Generated runtime statements, so we'll just
                            # run the whole loop at runtime.
                            generate_at_runtime = True
                            break
                    else:
                        # should never happen
                        raise Exception("boolean expr has non-boolean value")
                except NotConstantError:
                    # Test expression isn't constant, so we'll just run
                    # the whole loop at runtime.
                    generate_at_runtime = True
                    break

        if generate_at_runtime:
            # throw away the previous registry and this time force a runtime
            # loop to be generated by forcing the interpreter to delay
            # evaluating variables until runtime.
            registry = interpreter.child_registry()
            with registry:
                with interpreter.force_runtime():
                    test_expr = self.test_expr.evaluate()
                    runtime_block = self.block.execute()
                    runtime_stmt = WhileStmt(
                        self.position,
                        test_expr,
                        runtime_block,
                    )
                    runtime_stmts.append(runtime_stmt)

            # We don't know if the body will run at runtime
            interpreter.registry.merge_children([registry], or_none=True)
        else:
            # We know the loop ran to completion, so we can definitively
            # merge its state.
            interpreter.registry.merge_children([registry])

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
                    self.position,
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

    def execute(self, runtime_stmts):
        # A function declaration is really just a funny sort of
        # declaration that forces a function type.
        from alamatic.types import FunctionTemplate
        from alamatic.interpreter import interpreter

        # Need to retain the scope the function was declared in so that
        # we can execute its body in a child of it later.
        decl_scope = interpreter.symbols

        template_value = FunctionTemplate(self, decl_scope)

        interpreter.declare_and_init(
            self.decl.name,
            template_value,
            const=True,  # function templates are always constant
            position=self.position,
        )


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
