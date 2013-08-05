
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
        if type(eval_expr) != ValueExpr:
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
            SymbolStorageExpr,
            ConstDeclClause,
        )
        from alamatic.compilelogging import pos_link

        const = type(self.decl) is ConstDeclClause

        interpreter.declare(self.decl.name, const=const)
        if self.expr is None:
            if const:
                raise NotConstantError(
                    "Constant '%s'," % self.decl.name,
                    " declared at ", pos_link(self.position),
                    ", must be assigned an initial value",
                )
        else:
            val_expr = self.expr.evaluate()
            if type(val_expr) is ValueExpr:
                interpreter.assign(self.decl.name, val_expr.value)
            else:
                if const:
                    raise NotConstantError(
                        "Initial value for constant '%s'," % self.decl.name,
                        " declared at ", pos_link(self.position),
                        ", can't be determined at compile time",
                    )
                else:
                    interpreter.mark_unknown(
                        self.decl.name,
                        known_type=val_expr.result_type
                    )

            storage = interpreter.get_storage(self.decl.name)

            # The code generator will generate the declaration from the scope,
            # so we just need to assign a value to it in the runtime stmts.
            if not const:
                assign_stmt = ExpressionStmt(
                    self.position,
                    AssignExpr(
                        self.decl.position,
                        SymbolStorageExpr(
                            self,
                            storage,
                        ),
                        "=",
                        val_expr,
                    ),
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
