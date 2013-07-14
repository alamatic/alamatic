
from alamatic.scanner import Scanner
from alamatic.ast import *
from alamatic.compilelogging import pos_link, CompilerError


def parse_module(state, stream, name, filename):
    scanner = Scanner(state, stream, filename)

    stmts = p_statements(state, scanner, lambda s : s.next_is_eof())

    return Module((filename, 1, 0), name, stmts)


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

    expr = p_expression(state, scanner)
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


def p_expression(state, scanner):
    peek = scanner.peek()

    return p_expr_term(state, scanner)


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
        "Can't start an expression with ",
        scanner.token_display_name(scanner.peek()),
        " at ", pos_link(pos),
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
