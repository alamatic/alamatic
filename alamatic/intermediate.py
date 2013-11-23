
from alamatic.compilelogging import CompilerError, pos_link


class Symbol(object):
    def __init__(
        self,
        decl_table,
        decl_position=None,
    ):
        self.decl_table = decl_table
        self.decl_position = decl_position
        self.type = None
        self.init_position = None

    def make_operand(self, position=None):
        return SymbolOperand(
            self,
            position=position,
        )

    def __repr__(self):
        return '<alamatic.intermediate.%s>' % str(self)


class NamedSymbol(Symbol):

    def __init__(
        self,
        decl_table,
        decl_name,
        const=False,
        decl_position=None
    ):
        super(NamedSymbol, self).__init__(
            decl_table, decl_position=decl_position,
        )
        self.decl_name = decl_name
        self.const = const

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

    @property
    def codegen_name(self):
        return "_ala_%x" % id(self)

    def __str__(self):
        return '%s from %r' % (
            self.decl_name,
            self.decl_position,
        )


class TemporarySymbol(Symbol):

    def __init__(
        self,
        decl_table,
    ):
        super(TemporarySymbol, self).__init__(
            decl_table, decl_position=None,
        )

    @property
    def codegen_name(self):
        return "_tmp_%x" % id(self)

    def __str__(self):
        return 'temp(%x)' % (
            id(self),
        )


class SymbolTable(object):

    def __init__(self, parent=None):
        self.parent = parent
        self.children = []
        self.symbols = {}
        self.temporaries = []

    def lookup(self, name, position=None):
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

    def declare(self, name, const=False, position=None):
        symbol = self.begin_declare(name, const=const, position=position)
        self.complete_declare(symbol)
        return symbol

    def begin_declare(self, name, const=False, position=None):
        return NamedSymbol(self, name, const, position)

    def complete_declare(self, symbol):
        if isinstance(symbol, NamedSymbol):
            self.symbols[symbol.decl_name] = symbol
        else:
            # Should never happen
            raise Exception(
                "Can only complete declaration of a named symbol."
            )

    def create_temporary(self):
        symbol = TemporarySymbol(self)
        self.temporaries.append(symbol)
        return symbol

    def create_child(self):
        child = SymbolTable(self)
        self.children.append(child)
        return child


class Element(object):
    def __init__(self, position=None):
        self.position = position

    @property
    def params(self):
        return []

    def __str__(self):
        return type(self).__name__ + "(" + (', '.join(
            (str(x) for x in self.params)
        )) + " : " + repr(self.position) + ")"

    def __repr__(self):
        return "<alamatic.intermediate.%s>" % self.__str__()

    def generate_c_code(self, state, writer):
        raise Exception(
            "generate_c_code not implemented for %r" % self
        )


class Label(Element):
    pass


class Operation(Element):
    pass


class CopyOperation(Operation):

    def __init__(self, target, operand, position=None):
        self.target = target
        self.operand = operand
        self.position = position

    @property
    def params(self):
        yield self.target
        yield self.operand

    def generate_c_code(self, state, writer):
        self.target.generate_c_code(state, writer)
        writer.write(" = ")
        self.operand.generate_c_code(state, writer)
        writer.writeln(";")


class UnaryOperation(Operation):

    def __init__(self, target, operator, operand, position=None):
        self.target = target
        self.operator = operator
        self.operand = operand
        self.position = position


class BinaryOperation(Operation):
    def __init__(self, target, lhs, operator, rhs, position=None):
        self.target = target
        self.lhs = lhs
        self.operator = operator
        self.rhs = rhs
        self.position = position

    @property
    def params(self):
        yield self.target
        yield self.lhs
        yield self.operator
        yield self.rhs

    def generate_c_code(self, state, writer):
        self.target.generate_c_code(state, writer)
        writer.write(" = ")
        self.lhs.generate_c_code(state, writer)
        # FIXME: Assuming for now that intermediate operators are
        # one-to-one with C operators, which won't actually be true
        # in practice
        writer.write(" " + self.operator + " ")
        self.rhs.generate_c_code(state, writer)
        writer.writeln(";")


class CallOperation(Operation):
    def __init__(self, target, callee, args, position=None):
        self.target = target
        self.callee = callee
        self.args = args
        self.position = position


class AttributeLookupOperation(Operation):
    def __init__(self, target, operand, name, position=None):
        self.target = target
        self.operand = operand
        self.name = name
        self.position = position


class IndexOperation(Operation):
    def __init__(self, target, operand, index, position=None):
        self.target = target
        self.operand = operand
        self.index = index
        self.position = position


class SliceOperation(Operation):
    def __init__(self, target, operand, start_index, length, position=None):
        self.target = target
        self.operand = operand
        self.start_index = start_index
        self.length = length


class JumpOperation(Operation):
    def __init__(self, label, position=None):
        self.label = label
        self.position = position


class ConditionalJumpOperation(JumpOperation):
    def __init__(self, cond, label, position=None):
        self.cond = cond
        self.label = label
        self.position = position


class Operand(object):
    def __init__(self, position=None):
        self.position = position

    @property
    def params(self):
        return []

    def __str__(self):
        return type(self).__name__ + "(" + (', '.join(
            (str(x) for x in self.params)
        )) + " : " + repr(self.position) + ")"

    def __repr__(self):
        return "<alamatic.intermediate.%s>" % self.__str__()

    def generate_c_code(self, state, writer):
        raise Exception(
            "generate_c_code not implemented for %r" % self
        )


class ConstantOperand(Operand):
    # rvalue only
    def __init__(self, value, position=None):
        self.value = value
        self.position = position

    @property
    def params(self):
        yield self.value

    def generate_c_code(self, state, writer):
        self.value.generate_c_code(state, writer)


class SymbolOperand(Operand):
    # both lvalue and rvalue
    def __init__(self, symbol, position=None):
        self.symbol = symbol
        self.position = position

    @property
    def params(self):
        yield self.symbol

    def generate_c_code(self, state, writer):
        writer.write(self.symbol.codegen_name)


class IndexOperand(Operand):
    # lvalue only
    def __init__(self, source, index, position=None):
        self.source = source
        self.index = index
        self.position = position


class AttributeOperand(Operand):
    # lvalue only
    def __init__(self, source, name, position=None):
        self.source = source
        self.name = name
        self.position = position


class DereferenceOperand(Operand):
    # lvalue only
    def __init__(self, source, position=None):
        self.source = source
        self.position = position


class IncompatibleTypesError(CompilerError):
    pass


class UnknownSymbolError(CompilerError):
    pass


class NotConstantError(CompilerError):
    pass


class InvalidLValueError(CompilerError):
    pass
