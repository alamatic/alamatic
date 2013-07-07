
from alamatic.scanner import Scanner
from alamatic.ast import *


class ParseState(object):
    pass


def parse_module(state, stream, name, filename):
    scanner = Scanner(stream, filename)

    stmts = []
    while not scanner.next_is_eof():
        stmt = p_statement(state, scanner)
        if stmt is not None:
            stmts.append(stmt)

    return Module((filename, 1, 0), name, stmts)


def p_statement(state, scanner):
    pos = scanner.position()

    if scanner.next_is_newline():
        # empty statement
        scanner.read()
        return None

    # FIXME: Just a stub until we actually fill out the set of ast nodes
    # for statements.
    while not scanner.next_is_newline():
        scanner.read()
    scanner.require_newline()
    stmt = Statement()
    stmt.position = pos
    return stmt

