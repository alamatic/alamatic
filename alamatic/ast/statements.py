
from alamatic.ast import *


class Statement(AstNode):

    def make_intermediate_form(self, elems, parent_symbols):
        raise Exception(
            "make_intermediate_form is not implemented for %r" % self,
        )


class ExpressionStmt(Statement):

    def __init__(self, position, expr):
        self.position = position
        self.expr = expr

    @property
    def child_nodes(self):
        yield self.expr

    def make_intermediate_form(self, elems, symbols):
        from alamatic.intermediate import (
            SymbolOperand,
        )
        from alamatic.compilelogging import CompilerError, pos_link
        if not self.expr.can_be_statement:
            raise CompilerError(
                "Expression cannot be statement at ",
                pos_link(self.expr.position),
            )

        self.expr.make_intermediate_form(
            elems,
            symbols,
        )


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

    def make_intermediate_form(self, elems, symbols):
        from alamatic.intermediate import (
            Label,
            JumpOperation,
            JumpIfFalseOperation,
        )

        # FIXME: It would be better to use the position of the
        # end of the statement, but the parser doesn't currently
        # preserve that information.
        end_label = Label(position=self.position)

        for clause in self.clauses:
            if isinstance(clause, IfClause):
                # FIXME: It would be better to use the position of the
                # end of the clause, but the parser doesn't currently
                # preserve that information.
                skip_label = Label(position=clause.position)
                test_operand = clause.test_expr.make_intermediate_form(
                    elems, symbols,
                )
                elems.append(
                    JumpIfFalseOperation(
                        test_operand,
                        skip_label,
                        position=clause.position,
                    )
                )
                clause.block.make_intermediate_form(
                    elems, symbols,
                )
                elems.append(
                    JumpOperation(
                        end_label,
                        position=skip_label.position,
                    ),
                )
                elems.append(
                    skip_label
                )
            elif isinstance(clause, ElseClause):
                clause.block.make_intermediate_form(
                    elems, symbols,
                )

        elems.append(
            end_label
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

    def make_intermediate_form(self, elems, symbols):
        from alamatic.intermediate import (
            Label,
            JumpOperation,
            JumpIfFalseOperation,
        )

        head_label = Label(position=self.position)
        # FIXME: It'd be nicer to report the position of the
        # *end* of the loop here but the parser doesn't currently preserve
        # that information.
        end_label = Label(position=self.position)

        elems.append(head_label)

        test_operand = self.test_expr.make_intermediate_form(
            elems, symbols,
        )

        elems.append(
            JumpIfFalseOperation(
                test_operand,
                end_label,
                self.test_expr.position,
            )
        )

        self.block.make_intermediate_form(elems, symbols)

        elems.append(
            JumpOperation(
                head_label,
                position=end_label.position,
            )
        )
        elems.append(end_label)


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

    def make_intermediate_form(self, elems, symbols):
        from alamatic.intermediate import (
            SymbolOperand,
            NotConstantError,
            CopyOperation,
        )
        from alamatic.ast import (
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
                symbols.declare(
                    self.decl.name,
                    const=False,
                    position=self.position,
                )
        else:
            # We do a two-stage declaration here because we can't
            # put the new symbol in the symbol table until we've
            # analysed the declaration expression.
            symbol = symbols.begin_declare(
                self.decl.name,
                const=const,
                position=self.position,
            )
            assign_target = SymbolOperand(
                symbol,
                position=self.decl.position,
            )
            initializer = self.expr.make_intermediate_form(
                elems, symbols,
            )
            elems.append(
                CopyOperation(
                    assign_target,
                    initializer,
                    position=self.position,
                )
            )
            symbols.complete_declare(symbol)


class FuncDeclStmt(Statement):

    def __init__(self, position, decl, block):
        self.position = position
        self.decl = decl
        self.block = block

    @property
    def child_nodes(self):
        yield self.decl
        yield self.block

    def make_intermediate_form(self, elems, symbols):
        # A function declaration is really just a funny sort of
        # declaration that forces a function type.
        from alamatic.types import FunctionTemplate
        from alamatic.intermediate import (
            CopyOperation,
            ConstantOperand,
        )

        # Need to retain the scope the function was declared in so that
        # we can execute its body in a child of it later.
        decl_scope = symbols
        template_value = FunctionTemplate(self, decl_scope)

        symbol = symbols.declare(
            self.decl.name,
            const=True,  # function templates are always constant
            position=self.position,
        )
        elems.append(
            CopyOperation(
                symbol.make_operand(),
                ConstantOperand(
                    template_value,
                    position=self.position,
                )
            )
        )
