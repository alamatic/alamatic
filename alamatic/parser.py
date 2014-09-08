
from alamatic.scanner import Scanner
from alamatic.ast import *
from alamatic.compilelogging import pos_link, CompilerError


def parse_module(state, stream, name, filename):
    source_range, block, doc = p_toplevel(state, stream, filename)
    return Module(source_range, name, block, doc=doc)


def parse_entry_file(state, stream, filename):
    source_range, block, doc = p_toplevel(state, stream, filename)
    return EntryFile(source_range, block, doc=doc)


def p_toplevel(state, stream, filename):
    scanner = Scanner(state, stream, filename)

    full_range = scanner.begin_range()

    # doc comments at the immediate start of a module are for the
    # module itself.
    doc = p_doc_comments(state, scanner)

    # To avoid ambiguity, a newline is required after a module docstring.
    if doc is not None:
        if not (scanner.next_is_newline() or scanner.next_is_eof()):
            state.error(
                "Include a blank line after the module doc comments, ",
                "at ", pos_link(scanner.position()),
                " (if this was supposed to be a doc comment for the following "
                "statement instead, add a blank line before it.)"
            )
            # but we'll keep parsing anyway, in case there are some other
            # errors we could report at the same time.

    stmts = p_statements(state, scanner, lambda s: s.next_is_eof())
    block = StatementBlock(stmts)

    return full_range.end(), block, doc


def parse_expression(state, stream, filename, allow_assign=False):
    scanner = Scanner(state, stream, filename, expression_only=True)
    expr = None
    try:
        expr = p_expression(state, scanner, allow_assign=allow_assign)
        scanner.require_eof()
    except CompilerError, ex:
        state.error(ex)
    return expr


def p_doc_comments(state, scanner):
    peek = scanner.peek()
    if peek[0] == "DOCCOMMENT":
        parts = []
        while peek[0] == "DOCCOMMENT":
            scanner.read()
            parts.append(peek[1])
            scanner.require_newline()
            peek = scanner.peek()
        return "\n".join(parts)
    else:
        # no doc comments at all is signalled as None, to differentiate
        # between this case an an *empty* doc comment.
        return None


def p_statements(state, scanner, stop_test=lambda s: s.next_is_outdent()):
    stmts = []
    while not stop_test(scanner):
        stmt = None
        try:
            stmt = p_statement(state, scanner)
        except CompilerError, ex:
            state.error(ex)
            scanner.skip_statement()
        if stmt is not None:
            stmts.append(stmt)

    return stmts


def p_indented_block(state, scanner):
    scanner.require_punct(":")
    scanner.require_newline()
    scanner.require_indent()
    stmts = p_statements(state, scanner)
    scanner.require_outdent()
    return StatementBlock(stmts)


def p_expr_list(state, scanner, terminator_punct, allow_assign=False):
    exprs = []
    if scanner.next_is_punct(terminator_punct):
        scanner.read()
    else:
        while True:
            exprs.append(
                p_expression(state, scanner, allow_assign=allow_assign)
            )
            if scanner.next_is_punct(terminator_punct):
                scanner.read()
                break
            scanner.require_punct(",")
            if scanner.next_is_punct(terminator_punct):
                scanner.read()
                break

    return ExpressionList(exprs)


def p_arguments(state, scanner, terminator_punct):
    expr_list = p_expr_list(
        state, scanner, terminator_punct, allow_assign=True,
    )

    args = []
    kwargs = {}

    for expr in expr_list.exprs:
        if isinstance(expr, AssignExpr):
            if isinstance(expr.lhs, SymbolNameExpr):
                name = expr.lhs.name
                kwargs[name] = expr.rhs
            else:
                raise CompilerError(
                    "Invalid keyword argument at ",
                    pos_link(self.lhs.position),
                )
        else:
            args.append(expr)

    return Arguments(args, kwargs)


def p_statement(state, scanner):
    full_range = scanner.begin_range()

    if scanner.next_is_newline():
        # empty statement
        scanner.read()
        return None

    peek = scanner.peek()
    if peek[0] == "IDENT":
        ident = peek[1]
        if ident == "pass":
            scanner.read()
            scanner.require_newline()
            return PassStmt(full_range.end())
        if ident == "break":
            scanner.read()
            scanner.require_newline()
            return BreakStmt(full_range.end())
        if ident == "continue":
            scanner.read()
            scanner.require_newline()
            return ContinueStmt(full_range.end())
        if ident == "return":
            scanner.read()
            expr = None
            if not scanner.next_is_newline():
                expr = p_expression(state, scanner)
            scanner.require_newline()
            return ReturnStmt(full_range.end(), expr)
        if ident == "if":
            return p_if_stmt(state, scanner)
        if ident == "while":
            scanner.read()
            expr = p_expression(state, scanner)
            block = p_indented_block(state, scanner)
            return WhileStmt(full_range.end(), expr, block)
        if ident == "for":
            return p_for_stmt(state, scanner)
        if ident == "var" or ident == "const":
            decl = p_data_decl(state, scanner)
            expr = None
            if scanner.next_is_punct('='):
                scanner.read()
                expr = p_expression(state, scanner)
            scanner.require_newline()
            return DataDeclStmt(full_range.end(), decl, expr)
        if ident == "func":
            decl = p_func_decl(state, scanner)
            block = p_indented_block(state, scanner)
            return FuncDeclStmt(full_range.end(), decl, block)

    expr = p_expression(state, scanner, allow_assign=True)
    scanner.require_newline()
    # FIXME: Should fail if an expression statement has no
    # direct side-effects... that is, if it's not a call or an
    # assignment node.
    return ExpressionStmt(full_range.end(), expr)


def p_if_stmt(state, scanner):
    full_range = scanner.begin_range()

    clauses = []

    if_range = scanner.begin_range()
    scanner.require_keyword("if")
    if_expr = p_expression(state, scanner)
    if_block = p_indented_block(state, scanner)

    clauses.append(IfClause(if_range.end(), if_expr, if_block))

    while scanner.next_is_keyword("elif"):
        elif_range = scanner.begin_range()
        scanner.read()
        elif_expr = p_expression(state, scanner)
        elif_block = p_indented_block(state, scanner)
        clauses.append(IfClause(elif_range.end(), elif_expr, elif_block))

    if scanner.next_is_keyword("else"):
        else_range = scanner.begin_range()
        scanner.read()
        else_block = p_indented_block(state, scanner)
        clauses.append(ElseClause(else_range.end(), else_block))

    return IfStmt(full_range.end(), clauses)


def p_for_stmt(state, scanner):
    full_range = scanner.begin_range()

    scanner.require_keyword("for")
    if scanner.next_is_keyword("var") or scanner.next_is_keyword("const"):
        target = p_data_decl(state, scanner)
    else:
        target = p_expression(state, scanner)

    scanner.require_keyword("in")
    source_expr = p_expression(state, scanner)

    block = p_indented_block(state, scanner)

    return ForStmt(full_range.end(), target, source_expr, block)


def p_expression(state, scanner, allow_assign=False):
    peek = scanner.peek()

    if allow_assign:
        return p_expr_assign(state, scanner)
    else:
        # skip straight to logical or, which is the next operator in
        # precedence order
        return p_expr_logical_or(state, scanner)


def make_p_expr_binary_op(name, operator_map, next_parser, allow_chain=True):
    this_parser = None

    def this_parser(state, scanner):
        full_range = scanner.begin_range()

        lhs = next_parser(state, scanner)

        peek = scanner.peek()
        if peek[0] in ("IDENT", peek[1]) and peek[1] in operator_map:
            operator = peek[1]
            ast_class = operator_map[peek[1]]
        else:
            return lhs

        # Eat the operator token, since we already dealt with it above.
        scanner.read()

        # As a special case for the funky, two-token "is not" operator,
        # we try to eat up a "not" right after an "is".
        # (Yes, this is a bit of a hack. Oh well.)
        if operator == "is" and scanner.next_is_keyword("not"):
            operator = "is not"
            scanner.read()

        if allow_chain:
            rhs = this_parser(state, scanner)
        else:
            rhs = next_parser(state, scanner)

        return ast_class(full_range.end(), lhs, operator, rhs)

    this_parser.__name__ = name
    return this_parser


def make_p_expr_prefix_unary_op(name, operator_map, next_parser):
    this_parser = None

    def this_parser(state, scanner):
        full_range = scanner.begin_range()

        peek = scanner.peek()
        if peek[0] in ("IDENT", peek[1]) and peek[1] in operator_map:
            operator = peek[1]
            ast_class = operator_map[peek[1]]
            scanner.read()
            # Try running ourselves again so that we can chain,
            # like "not not a". Isn't incredibly useful but it ought to
            # work anyway for consistency.
            operand = this_parser(state, scanner)
            return ast_class(full_range.end(), operand, operator)
        else:
            return next_parser(state, scanner)

    this_parser.__name__ = name
    return this_parser


def p_expr_factor(state, scanner):
    source_range = scanner.begin_range()

    ret_expr = None

    ident_literals = {
        "true": True,
        "false": False,
        "null": None,
    }

    if scanner.next_is_punct("("):
        scanner.read()
        ret_expr = p_expression(state, scanner)
        scanner.require_punct(")")
    else:
        peek = scanner.peek()

        if peek[0] == "NUMBER":
            ret_expr = p_expr_number(state, scanner)
        elif peek[0] == "STRINGLIT":
            ret_expr = p_expr_string(state, scanner)
        elif peek[0] == "IDENT":
            scanner.read()
            if peek[1] in ident_literals:
                ret_expr = LiteralExpr(
                    source_range.end(),
                    ident_literals[peek[1]],
                )
            else:
                ret_expr = SymbolNameExpr(source_range.end(), peek[1])
        else:
            raise CompilerError(
                "Expected expression but found ",
                scanner.token_display_name(scanner.peek()),
                " at ", pos_link(source_range.start),
            )

    # Now handle calls, subscripts and attribute access, if present.
    # These can be chained indefinitely.
    while True:
        if scanner.next_is_punct("("):
            scanner.read()
            args = p_arguments(state, scanner, ")")
            ret_expr = CallExpr(
                source_range.end(),
                ret_expr,
                args,
            )
        elif scanner.next_is_punct("["):
            scanner.read()
            args = p_expr_list(state, scanner, "]")
            ret_expr = SubscriptExpr(
                source_range.end(),
                ret_expr,
                args,
            )
        elif scanner.next_is_punct("."):
            scanner.read()
            if scanner.peek()[0] != "IDENT":
                raise CompilerError(
                    "Expected attribute name but got ",
                    scanner.token_display_name(scanner.peek()),
                    " at ", pos_link(scanner.position()),
                )
            attr_name = scanner.read()[1]
            ret_expr = AttributeExpr(
                source_range.end(),
                ret_expr,
                attr_name,
            )
        else:
            break

    return ret_expr


p_expr_bitwise_not = make_p_expr_prefix_unary_op(
    "p_expr_bitwise_not",
    {
        "~": BitwiseNotExpr,
    },
    p_expr_factor,
)


p_expr_sign = make_p_expr_prefix_unary_op(
    "p_expr_sign",
    {
        "-": SignExpr,
        "+": SignExpr,
    },
    p_expr_bitwise_not,
)


p_expr_multiply = make_p_expr_binary_op(
    "p_expr_multiply",
    {
        "*": MultiplyExpr,
        "/": MultiplyExpr,
        "%": MultiplyExpr,
    },
    p_expr_sign,
)


p_expr_sum = make_p_expr_binary_op(
    "p_expr_sum",
    {
        "+": SumExpr,
        "-": SumExpr,
    },
    p_expr_multiply,
)


p_expr_shift = make_p_expr_binary_op(
    "p_expr_shift",
    {
        "<<": ShiftExpr,
        ">>": ShiftExpr,
    },
    p_expr_sum,
)


p_expr_bitwise_and = make_p_expr_binary_op(
    "p_expr_bitwise_and",
    {
        "&": BitwiseAndExpr,
    },
    p_expr_shift,
)


p_expr_bitwise_or = make_p_expr_binary_op(
    "p_expr_bitwise_or",
    {
        "|": BitwiseOrExpr,
    },
    p_expr_bitwise_and,
)


p_expr_comparison = make_p_expr_binary_op(
    "p_expr_comparison",
    {

        "is": ComparisonExpr,
        # A special case inside make_p_expr_binary_op allows
        # "is" to also implement "is not". (Hacky, yes.)

        "<": ComparisonExpr,
        "<=": ComparisonExpr,
        ">": ComparisonExpr,
        ">=": ComparisonExpr,
        "!=": ComparisonExpr,
        "==": ComparisonExpr,
    },
    p_expr_bitwise_or,
)


p_expr_logical_not = make_p_expr_prefix_unary_op(
    "p_expr_logical_not",
    {
        "not": LogicalNotExpr,
    },
    p_expr_comparison,
)


p_expr_logical_and = make_p_expr_binary_op(
    "p_expr_logical_and",
    {
        "and": LogicalAndExpr,
    },
    p_expr_logical_not,
)


p_expr_logical_or = make_p_expr_binary_op(
    "p_expr_logical_or",
    {
        "or": LogicalOrExpr,
    },
    p_expr_logical_and,
)


p_expr_assign = make_p_expr_binary_op(
    "p_expr_assign",
    {
        "=": AssignExpr,
        "+=": AssignExpr,
        "-=": AssignExpr,
        "*=": AssignExpr,
        "/=": AssignExpr,
        "|=": AssignExpr,
        "&=": AssignExpr,
    },
    p_expr_logical_or,
    allow_chain=False,
)


def p_expr_number(state, scanner):
    full_range = scanner.begin_range()

    token = scanner.read()
    if token[0] != "NUMBER":
        raise CompilerError(
            "Expected number but got ",
            scanner.token_display_name(token),
            " at ", pos_link(full_range.start),
        )

    num_str = token[1]

    if num_str.startswith("0x"):
        try:
            value = int(num_str[2:], 16)
        except ValueError:
            raise CompilerError(
                num_str[2:], " is not a valid hexadecimal number, "
                " at ", pos_link(full_range.start),
            )
    elif num_str.startswith("0b"):
        try:
            value = int(num_str[2:], 2)
        except ValueError:
            raise CompilerError(
                num_str[2:], " is not a valid binary number, "
                " at ", pos_link(full_range.start),
            )
    elif num_str.startswith("0") and len(num_str) > 1:
        try:
            value = int(num_str[1:], 8)
        except ValueError:
            raise CompilerError(
                num_str[1:], " is not a valid octal number, "
                " at ", pos_link(full_range.start),
            )
    else:
        # Try to parse it as a base-10 int, and if that fails
        # try to parse as a float. If neither work, fail hard.
        try:
            value = int(num_str, 10)
        except ValueError:
            try:
                value = float(num_str)
            except ValueError:
                raise CompilerError(
                    num_str, " is not a valid number, "
                    " at ", pos_link(full_range.start),
                )

    if value is None:
        # Should never happen
        raise Exception(
            "Failed to produce a value for number token " + num_str
        )

    return LiteralExpr(full_range.end(), value)


def p_data_decl(state, scanner):
    full_range = scanner.begin_range()

    if scanner.next_is_keyword("var"):
        decl_type = VarDeclClause
    elif scanner.next_is_keyword("const"):
        decl_type = ConstDeclClause
    else:
        raise CompilerError(
            "Expected declaration but got ",
            scanner.token_display_name(scanner.peek()),
            " at ", pos_link(full_range.start),
        )

    scanner.read()

    if scanner.peek()[0] != "IDENT":
        raise CompilerError(
            "Expected declaration name but got ",
            scanner.token_display_name(scanner.peek()),
            " at ", pos_link(scanner.position()),
        )

    name = scanner.read()[1]

    return decl_type(full_range.end(), name)


def p_func_decl(state, scanner):
    full_range = scanner.begin_range()

    scanner.require_keyword("func")

    if scanner.peek()[0] != "IDENT":
        raise CompilerError(
            "Expected function name but got ",
            scanner.token_display_name(scanner.peek()),
            " at ", pos_link(scanner.position()),
        )

    name = scanner.read()[1]

    params = []
    scanner.require_punct("(")
    if scanner.next_is_punct(")"):
        scanner.read()
    else:
        while True:
            if scanner.peek()[0] != "IDENT":
                raise CompilerError(
                    "Expected parameter name but got ",
                    scanner.token_display_name(scanner.peek()),
                    " at ", pos_link(scanner.position()),
                )
            param_range = scanner.begin_range()
            param_const = False
            param_named = False
            param_collector = False
            param_default_expr = None
            param_type_constraint_expr = None

            if scanner.next_is_keyword("const"):
                scanner.read()
                param_const = True

            if scanner.next_is_keyword("named"):
                scanner.read()
                param_named = True

            if scanner.next_is_keyword("const"):
                if param_named:
                    raise CompilerError(
                        "'const' qualifier must appear before 'named',",
                        " not at ", pos_link(scanner.position()),
                    )
                else:
                    raise CompilerError(
                        "Parameter must not be called 'const' at ",
                        pos_link(scanner.position()),
                    )

            param_name = scanner.read()[1]

            if scanner.next_is_punct("="):
                scanner.read()
                param_default_expr = p_expression(state, scanner)

            if scanner.next_is_keyword("when"):
                scanner.read()
                param_type_constraint_expr = p_expression(state, scanner)

            if scanner.next_is_punct("..."):
                scanner.read()
                param_collector = True

            params.append(
                ParamDeclClause(
                    param_range.end(),
                    param_name,
                    const_required=param_const,
                    named=param_named,
                    default_expr=param_default_expr,
                    collector=param_collector,
                    type_constraint_expr=param_type_constraint_expr,
                )
            )

            if scanner.next_is_punct(")"):
                scanner.read()
                break
            scanner.require_punct(",")
            if scanner.next_is_punct(")"):
                scanner.read()
                break

    return FuncDeclClause(full_range.end(), name, params)
