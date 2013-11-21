
from alamatic.compilelogging import CompilerError, pos_link


class Symbol(object):

    def __init__(self, decl_table=None, decl_name=None, decl_position=None):
        self.decl_table = decl_table
        self.decl_name = decl_name
        self.decl_position = decl_position
        self.type = None
        self.init_position = None
        self.const = None
        self.latest_version = None

    def initialize(self, type_, const=False, position=None):
        if self.type is None:
            self.type = type_
            self.const = const
            self.init_position = position
        else:
            # Should never happen
            raise Exception(
                "Symbol already initialized"
            )

    def get_version(self):
        self.latest_version += 1
        return self.latest_version


class SymbolTable(object):

    def __init__(self, parent=None):
        self.parent = parent
        self.symbols = {}

    def lookup(name, position=None):
        current = self
        while current is not None:
            try:
                return current.symbols[name]
            except KeyError:
                pass
        raise UnknownSymbolError(
            "Unknown symbol '%s' at " % name,
            pos_link(position),
        )


class Element(object):
    def __init__(self, position=None):
        self.position = position


class Label(Element):
    pass


class Operation(Element):
    pass


class UnaryOperation(Operation):

    def __init__(self, target, operand, position=None):
        self.target = target
        self.operand = operand
        self.position = position


class BinaryOperation(Operation):
    def __init__(self, target, lhs, rhs, position=None):
        self.target = target
        self.lhs = lhs
        self.rhs = rhs
        self.position = position


class CallOperation(Operation):
    def __init__(self, target, callee, args, position=None):
        self.target = target
        self.callee = callee
        self.args = args
        self.position = position


class JumpOperation(Operation):
    def __init__(self, label, position=None):
        self.label = label
        self.position = position


class ForwardJumpOperation(JumpOperation):
    pass


class BackwardJumpOperation(JumpOperation):
    pass


class IncompatibleTypesError(CompilerError):
    pass


class UnknownSymbolError(CompilerError):
    pass
