
from alamatic.scanner import Scanner
from alamatic.ast import *
from alamatic.compilelogging import pos_link, CompilerError


def parse_module(state, stream, name, filename):
    scanner = Scanner(state, stream, filename)

    stmts = p_statements(state, scanner, lambda s : s.next_is_eof())

    return Module((filename, 1, 0), name, stmts)


def parse_expression(state, stream, filename, allow_assign=False):
    scanner = Scanner(state, stream, filename, expression_only=True)
    expr = None
    try:
        expr = p_expression(state, scanner, allow_assign=allow_assign)
        scanner.require_eof()
    except CompilerError, ex:
        state.error(ex)
    return expr


def p_statements(state, scanner, stop_test=lambda s : s.next_is_outdent()):
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
    return stmts


def p_statement(state, scanner):
    pos = scanner.position()

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
            return PassStmt(pos)
        if ident == "break":
            scanner.read()
            scanner.require_newline()
            return BreakStmt(pos)
        if ident == "continue":
            scanner.read()
            scanner.require_newline()
            return ContinueStmt(pos)
        if ident == "return":
            scanner.read()
            expr = None
            if not scanner.next_is_newline():
                expr = p_expression(state, scanner)
            scanner.require_newline()
            return ReturnStmt(pos, expr)
        if ident == "if":
            return p_if_stmt(state, scanner)
        if ident == "while":
            scanner.read()
            expr = p_expression(state, scanner)
            stmts = p_indented_block(state, scanner)
            return WhileStmt(pos, expr, stmts)
        if ident == "for":
            return p_for_stmt(state, scanner)
        if ident == "var" or ident == "const":
            decl = p_data_decl(state, scanner)
            expr = None
            if scanner.next_is_punct('='):
                scanner.read()
                expr = p_expression(state, scanner)
            scanner.require_newline()
            return DataDeclStmt(pos, decl, expr)
        if ident == "func":
            decl = p_func_decl(state, scanner)
            stmts = p_indented_block(state, scanner)
            return FuncDeclStmt(pos, decl, stmts)

    expr = p_expression(state, scanner, allow_assign=True)
    scanner.require_newline()
    return ExpressionStmt(pos, expr)


def p_if_stmt(state, scanner):
    pos = scanner.position()

    clauses = []

    if_pos = scanner.position()
    scanner.require_keyword("if")
    if_expr = p_expression(state, scanner)
    if_stmts = p_indented_block(state, scanner)

    clauses.append(IfClause(if_pos, if_expr, if_stmts))

    while scanner.next_is_keyword("elif"):
        elif_pos = scanner.position()
        scanner.read()
        elif_expr = p_expression(state, scanner)
        elif_stmts = p_indented_block(state, scanner)
        clauses.append(IfClause(elif_pos, elif_expr, elif_stmts))

    if scanner.next_is_keyword("else"):
        else_pos = scanner.position()
        scanner.read()
        else_stmts = p_indented_block(state, scanner)
        clauses.append(ElseClause(else_pos, else_stmts))

    return IfStmt(pos, clauses)


def p_for_stmt(state, scanner):
    pos = scanner.position()

    scanner.require_keyword("for")
    if scanner.next_is_keyword("var") or scanner.next_is_keyword("const"):
        target = p_data_decl(state, scanner)
    else:
        target = p_expression(state, scanner)

    scanner.require_keyword("in")
    source_expr = p_expression(state, scanner)

    stmts = p_indented_block(state, scanner)

    return ForStmt(pos, target, source_expr, stmts)


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
        pos = scanner.position()

        lhs = next_parser(state, scanner)

        peek = scanner.peek()
        if  peek[0] in ("IDENT", peek[1]) and peek[1] in operator_map:
            operator = peek[1]
            ast_class = operator_map[peek[1]]
        else:
            return lhs

        # Eat the operator token, since we already dealt with it above.
        scanner.read()

        if allow_chain:
            rhs = this_parser(state, scanner)
        else:
            rhs = next_parser(state, scanner)

        return ast_class(pos, lhs, operator, rhs)

    this_parser.__name__ = name
    return this_parser


def make_p_expr_prefix_unary_op(name, operator_map, next_parser):
    this_parser = None
    def this_parser(state, scanner):
        pos = scanner.position()

        peek = scanner.peek()
        if peek[0] in ("IDENT", peek[1]) and peek[1] in operator_map:
            operator = peek[1]
            ast_class = operator_map[peek[1]]
            scanner.read()
            # Try running ourselves again so that we can chain,
            # like "not not a". Isn't incredibly useful but it ought to
            # work anyway for consistency.
            operand = this_parser(state, scanner)
            return ast_class(pos, operand, operator)
        else:
            return next_parser(state, scanner)

    this_parser.__name__ = name
    return this_parser


def p_expr_term(state, scanner):
    pos = scanner.position()

    if scanner.next_is_punct("("):
        scanner.read()
        expr = p_expression(state, scanner)
        scanner.require_punct(")")
        return expr

    peek = scanner.peek()

    if peek[0] == "NUMBER":
        return p_expr_number(state, scanner)

    if peek[0] == "STRINGLIT":
        return p_expr_string(state, scanner)

    if peek[0] == "IDENT":
        scanner.read()
        return SymbolExpr(pos, peek[1])

    raise CompilerError(
        "Expected expression but found ",
        scanner.token_display_name(scanner.peek()),
        " at ", pos_link(pos),
    )


p_expr_bitwise_not = make_p_expr_prefix_unary_op(
    "p_expr_bitwise_not",
    {
        "~": BitwiseNotExpr,
    },
    p_expr_term,
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
        # TODO: Implement these ones.
        # (but "is not" will require a special case because it's
        # the only operator that consists of two tokens)
        #"is": LogicalIsExpr,
        #"is not": LogicalIsExpr,

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
    pos = scanner.position()

    token = scanner.read()
    if token[0] != "NUMBER":
        raise CompilerError(
            "Expected number but got ",
            scanner.token_display_name(token),
            " at ", pos_link(pos),
        )

    num_str = token[1]

    if num_str.startswith("0x"):
        try:
            value = int(num_str[2:], 16)
        except ValueError:
            raise CompilerError(
                num_str[2:], " is not a valid hexadecimal number, "
                " at ", pos_link(pos),
            )
    elif num_str.startswith("0b"):
        try:
            value = int(num_str[2:], 2)
        except ValueError:
            raise CompilerError(
                num_str[2:], " is not a valid binary number, "
                " at ", pos_link(pos),
            )
    elif num_str.startswith("0"):
        try:
            value = int(num_str[1:], 8)
        except ValueError:
            raise CompilerError(
                num_str[1:], " is not a valid octal number, "
                " at ", pos_link(pos),
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
                    " at ", pos_link(pos),
                )

    if value is None:
        # Should never happen
        raise Exception(
            "Failed to produce a value for number token " + num_str
        )

    if type(value) in (int, long):
        return IntegerLiteralExpr(pos, value)
    else:
        return FloatLiteralExpr(pos, value)


def p_data_decl(state, scanner):
    pos = scanner.position()

    if scanner.next_is_keyword("var"):
        decl_type = VarDeclClause
    elif scanner.next_is_keyword("const"):
        decl_type = ConstDeclClause
    else:
        raise CompilerError(
            "Expected declaration but got ",
            scanner.token_display_name(scanner.peek()),
            " at ", pos_link(pos),
        )

    scanner.read()

    if scanner.peek()[0] != "IDENT":
        raise CompilerError(
            "Expected declaration name but got ",
            scanner.token_display_name(scanner.peek()),
            " at ", pos_link(scanner.position()),
        )

    name = scanner.read()[1]

    return decl_type(pos, name)


def p_func_decl(state, scanner):
    pos = scanner.position()

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
            arg_pos = scanner.position()
            arg_name = scanner.read()[1]
            arg_type_expr = None
            if scanner.next_is_keyword("as"):
                scanner.read()
                arg_type_expr = p_expression(state, scanner)
            params.append(ParamDeclClause(arg_pos, arg_name, arg_type_expr))

            if scanner.next_is_punct(")"):
                scanner.read()
                break
            scanner.require_punct(",")
            if scanner.next_is_punct(")"):
                scanner.read()
                break

    return FuncDeclClause(pos, name, params)
