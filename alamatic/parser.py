
from alamatic.scanner import Scanner
from alamatic.ast import *
from alamatic.compilelogging import pos_link, CompilerError


def parse_module(state, stream, name, filename):
    scanner = Scanner(state, stream, filename)

    stmts = []
    while not scanner.next_is_eof():
        stmt = None
        try:
            stmt = p_statement(state, scanner)
        except CompilerError, ex:
            state.error(ex)
            scanner.skip_statement()
        if stmt is not None:
            stmts.append(stmt)

    return Module((filename, 1, 0), name, stmts)


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
            return PassStatement(pos)

    else:
        raise CompilerError(
            "Can't start a statement with ",
            scanner.token_display_name(scanner.peek()),
            " at ", pos_link(pos),
        )
