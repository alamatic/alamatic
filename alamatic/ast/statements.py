
from alamatic.ast import *


class Statement(AstNode):

    def make_intermediate_form(self, elems, parent_symbols):
        raise Exception(
            "make_intermediate_form is not implemented for %r" % self,
        )


class ExpressionStmt(Statement):

    def __init__(self, source_range, expr):
        self.source_range = source_range
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
                pos_link(self.expr.source_range),
            )

        self.expr.make_intermediate_form(
            elems,
            symbols,
        )


class PassStmt(Statement):
    pass


class LoopJumpStmt(Statement):

    from alamatic.compilelogging import CompilerError, pos_link

    class NotInLoopError(CompilerError):
        pass

    def make_intermediate_form(self, elems, symbols):
        from alamatic.intermediate import (
            JumpInstruction,
        )
        label = self.get_target_label(symbols)
        if label is not None:
            elems.append(
                JumpInstruction(
                    label,
                    source_range=self.source_range,
                ),
            )
        else:
            raise self.NotInLoopError(
                "Attempted to '%s' outside of a loop at " % (
                    self.jump_type_name
                ),
                self.pos_link(self.source_range),
            )


class BreakStmt(LoopJumpStmt):

    def get_target_label(self, symbols):
        return symbols.break_label

    @property
    def jump_type_name(self):
        return 'break'


class ContinueStmt(LoopJumpStmt):

    def get_target_label(self, symbols):
        return symbols.continue_label

    @property
    def jump_type_name(self):
        return 'continue'


class ReturnStmt(Statement):

    def __init__(self, source_range, expr=None):
        self.source_range = source_range
        self.expr = expr

    @property
    def child_nodes(self):
        if self.expr is not None:
            yield self.expr


class IfStmt(Statement):

    def __init__(self, source_range, clauses):
        self.source_range = source_range
        self.clauses = clauses

    @property
    def child_nodes(self):
        for clause in self.clauses:
            yield clause

    def make_intermediate_form(self, elems, symbols):
        from alamatic.intermediate import (
            Label,
            JumpInstruction,
            JumpIfFalseInstruction,
        )

        # FIXME: It would be better to use the source_range of the
        # end of the statement, but the parser doesn't currently
        # preserve that information.
        end_label = Label(source_range=self.source_range)

        for clause in self.clauses:
            if isinstance(clause, IfClause):
                # FIXME: It would be better to use the source_range of the
                # end of the clause, but the parser doesn't currently
                # preserve that information.
                skip_label = Label(source_range=clause.source_range)
                test_operand = clause.test_expr.make_intermediate_form(
                    elems, symbols,
                )
                elems.append(
                    JumpIfFalseInstruction(
                        test_operand,
                        skip_label,
                        source_range=clause.source_range,
                    )
                )
                clause.block.make_intermediate_form(
                    elems, symbols,
                )
                elems.append(
                    JumpInstruction(
                        end_label,
                        source_range=skip_label.source_range,
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

    def __init__(self, source_range, test_expr, block):
        self.source_range = source_range
        self.test_expr = test_expr
        self.block = block

    @property
    def child_nodes(self):
        yield self.test_expr
        yield self.block


class ElseClause(AstNode):

    def __init__(self, source_range, block):
        self.source_range = source_range
        self.block = block

    @property
    def child_nodes(self):
        yield self.block


class WhileStmt(Statement):

    def __init__(self, source_range, test_expr, block):
        self.source_range = source_range
        self.test_expr = test_expr
        self.block = block

    @property
    def child_nodes(self):
        yield self.test_expr
        yield self.block

    def make_intermediate_form(self, elems, symbols):
        from alamatic.intermediate import (
            Label,
            JumpInstruction,
            JumpIfFalseInstruction,
        )

        head_label = Label(source_range=self.source_range)
        # FIXME: It'd be nicer to report the source_range of the
        # *end* of the loop here but the parser doesn't currently preserve
        # that information.
        end_label = Label(source_range=self.source_range)

        elems.append(head_label)

        test_operand = self.test_expr.make_intermediate_form(
            elems, symbols,
        )

        elems.append(
            JumpIfFalseInstruction(
                test_operand,
                end_label,
                self.test_expr.source_range,
            )
        )

        body_symbols = symbols.create_child()
        body_symbols.break_label = end_label
        body_symbols.continue_label = head_label

        self.block.make_intermediate_form(elems, body_symbols)

        elems.append(
            JumpInstruction(
                head_label,
                source_range=end_label.source_range,
            )
        )
        elems.append(end_label)


class ForStmt(Statement):

    def __init__(self, source_range, target, source_expr, block):
        # target is either a variable declaration or an lvalue expression
        self.source_range = source_range
        self.target = target
        self.source_expr = source_expr
        self.block = block

    @property
    def child_nodes(self):
        yield self.target
        yield self.source_expr
        yield self.block


class DataDeclStmt(Statement):

    def __init__(self, source_range, decl, expr):
        self.source_range = source_range
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
            OperationInstruction,
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
                    " declared at ", pos_link(self.source_range),
                    ", must be assigned an initial value",
                )
            else:
                # Create symbol but leave it uninitialized
                symbols.declare(
                    self.decl.name,
                    const=False,
                    source_range=self.source_range,
                )
        else:
            # We do a two-stage declaration here because we can't
            # put the new symbol in the symbol table until we've
            # analysed the declaration expression.
            symbol = symbols.begin_declare(
                self.decl.name,
                const=const,
                source_range=self.source_range,
            )
            assign_target = SymbolOperand(
                symbol,
                source_range=self.decl.source_range,
            )
            initializer = self.expr.make_intermediate_form(
                elems, symbols,
            )
            elems.append(
                OperationInstruction(
                    assign_target,
                    CopyOperation(
                        initializer,
                    ),
                    source_range=self.source_range,
                )
            )
            symbols.complete_declare(symbol)


class FuncDeclStmt(Statement):

    def __init__(self, source_range, decl, block):
        self.source_range = source_range
        self.decl = decl
        self.block = block

    @property
    def child_nodes(self):
        yield self.decl
        yield self.block

    def make_intermediate_form(self, elems, symbols):
        # A function declaration is really just a funny sort of
        # declaration that forces a function type.
        from alamatic.intermediate import (
            OperationInstruction,
            CopyOperation,
            ConstantOperand,
            FunctionTemplate,
        )

        # Need to retain the scope the function was declared in so that
        # we can execute its body in a child of it later.
        decl_scope = symbols
        template_value = FunctionTemplate(self, decl_scope)

        symbol = symbols.declare(
            self.decl.name,
            const=True,  # function templates are always constant
            source_range=self.source_range,
        )
        elems.append(
            OperationInstruction(
                symbol.make_operand(),
                CopyOperation(
                    ConstantOperand(
                        template_value,
                    )
                ),
                source_range=self.source_range,
            )
        )
