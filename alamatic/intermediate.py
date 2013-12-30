
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
        index=None,
    ):
        super(TemporarySymbol, self).__init__(
            decl_table, decl_position=None,
        )
        self.index = index

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
        self.next_temporary_index = 1
        self._break_label = None
        self._continue_label = None

    def lookup(self, name, position=None):
        current = self
        while current is not None:
            try:
                return current.symbols[name]
            except KeyError:
                current = current.parent
        raise UnknownSymbolError(
            "Unknown symbol '%s' at " % name,
            pos_link(position),
        )

    @property
    def break_label(self):
        current = self
        while current is not None:
            if current._break_label is not None:
                return current._break_label
            current = current.parent
        return None

    @break_label.setter
    def break_label(self, value):
        self._break_label = value

    @property
    def continue_label(self):
        current = self
        while current is not None:
            if current._continue_label is not None:
                return current._continue_label
            current = current.parent
        return None

    @continue_label.setter
    def continue_label(self, value):
        self._continue_label = value

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
        index = self.next_temporary_index
        self.next_temporary_index += 1
        symbol = TemporarySymbol(self, index)
        self.temporaries.append(symbol)
        return symbol

    def create_child(self):
        child = SymbolTable(self)
        self.children.append(child)
        return child


class Element(object):
    position = None

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

    def generate_c_code(self, state, writer):
        writer.writeln("%s:" % self.codegen_name)

    @property
    def codegen_name(self):
        return "_ALA_%x" % id(self)

    def replace_operands(self, replace):
        pass


class Operation(Element):
    def generate_c_code(self, state, writer):
        writer.indent()
        self._generate_c_code(state, writer)
        writer.writeln(";")
        writer.outdent()

    def _generate_c_code(self, state, writer):
        raise Exception(
            "_generate_c_code not implemented for %r" % self
        )


class CopyOperation(Operation):

    def __init__(self, target, operand, position=None):
        self.target = target
        self.operand = operand
        self.position = position

    @property
    def params(self):
        yield self.target
        yield self.operand

    def replace_operands(self, replace):
        self.target = replace(self.target)
        self.operand = replace(self.operand)

    def _generate_c_code(self, state, writer):
        self.target.generate_c_code(state, writer)
        writer.write(" = ")
        self.operand.generate_c_code(state, writer)


class UnaryOperation(Operation):

    def __init__(self, target, operator, operand, position=None):
        self.target = target
        self.operator = operator
        self.operand = operand
        self.position = position

    def replace_operands(self, replace):
        self.target = replace(self.target)
        self.operand = replace(self.operand)


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

    def replace_operands(self, replace):
        self.target = replace(self.target)
        self.lhs = replace(self.lhs)
        self.rhs = replace(self.rhs)

    def _generate_c_code(self, state, writer):
        self.target.generate_c_code(state, writer)
        writer.write(" = ")
        self.lhs.generate_c_code(state, writer)
        # FIXME: Assuming for now that intermediate operators are
        # one-to-one with C operators, which won't actually be true
        # in practice
        writer.write(" " + self.operator + " ")
        self.rhs.generate_c_code(state, writer)


class CallOperation(Operation):
    def __init__(self, target, callee, args, kwargs, position=None):
        self.target = target
        self.callee = callee
        self.args = args
        self.kwargs = kwargs
        self.position = position

    @property
    def params(self):
        yield self.target
        yield self.callee
        yield self.args
        yield self.kwargs

    def replace_operands(self, replace):
        self.target = replace(self.target)
        self.callee = replace(self.callee)
        for i, arg in enumerate(self.args):
            self.args[i] = replace(self.args[i])
        for k, arg in self.kwargs.iteritems():
            self.kwargs[k] = replace(self.kwargs[k])

    def _generate_c_code(self, state, writer):
        if len(self.kwargs):
            # Should never happen - kwargs should get transformed into
            # flat args by the time we get to code generation.
            raise Exception(
                "Can't generate C code for call with kwargs",
            )
        self.target.generate_c_code(state, writer)
        writer.write(" = ")
        self.callee.generate_c_code(state, writer)
        writer.write("(")
        first = True
        for arg in self.args:
            if first:
                first = False
            else:
                writer.write(", ")
            arg.generate_c_code(state, writer)
        writer.write(")")


class AttributeLookupOperation(Operation):
    def __init__(self, target, operand, name, position=None):
        self.target = target
        self.operand = operand
        self.name = name
        self.position = position

    def replace_operands(self, replace):
        self.target = replace(self.target)
        self.operand = replace(self.operand)


class IndexOperation(Operation):
    def __init__(self, target, operand, index, position=None):
        self.target = target
        self.operand = operand
        self.index = index
        self.position = position

    def replace_operands(self, replace):
        self.target = replace(self.target)
        self.operand = replace(self.operand)


class SliceOperation(Operation):
    def __init__(self, target, operand, start_index, length, position=None):
        self.target = target
        self.operand = operand
        self.start_index = start_index
        self.length = length

    def replace_operands(self, replace):
        self.target = replace(self.target)
        self.operand = replace(self.operand)


class JumpOperation(Operation):
    def __init__(self, label, position=None):
        self.label = label
        self.position = position

    @property
    def params(self):
        yield self.label

    def _generate_c_code(self, state, writer):
        writer.write("goto %s" % self.label.codegen_name)

    def replace_operands(self, replace):
        pass

    @property
    def can_fall_through(self):
        return False

    @property
    def jump_targets(self):
        return set([self.label])


class JumpIfFalseOperation(JumpOperation):
    def __init__(self, cond, label, position=None):
        self.cond = cond
        self.label = label
        self.position = position

    @property
    def params(self):
        yield self.cond
        yield self.label

    def _generate_c_code(self, state, writer):
        writer.write("if (! ")
        self.cond.generate_c_code(state, writer)
        writer.write(") goto %s" % self.label.codegen_name)

    def replace_operands(self, replace):
        self.cond = replace(self.cond)

    @property
    def can_fall_through(self):
        return True

    @property
    def jump_targets(self):
        return set([self.label])


# This is not a "real" operation that should show up during code generation,
# but is used by the code analyzer to ensure that all basic blocks have
# a terminator, even if a particular block does not end with an explicit jump
# in the original IR.
class JumpNeverOperation(JumpOperation):
    def __init__(self):
        pass

    @property
    def params(self):
        return []

    def generate_c_code(self, state, writer):
        # nothing to generate, since this is just a no-op
        pass

    @property
    def can_fall_through(self):
        return True

    @property
    def jump_targets(self):
        return set()


class Operand(object):
    position = None

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


def simplify_temporaries_in_element_list(input_elems):
    """
    Removes unnecessary temporaries from a list of intermediate code elements.

    The mechanism by which we translate expressions to intermediate code
    causes a proliferation of temporaries that are not strictly necessary.
    This function takes the raw element list from intermediate code generation
    and returns a new element list that is functionally equivalent but with
    the unnecessary temporaries removed.
    """
    ret_elems = []

    # First we locate all of the redundant temporaries. A temporary is
    # redundant if it appears as the target of a copy operation, since
    # in that case the operand of the copy can be used in place of the
    # temporary in the following operations.
    # This assumes that each temporary is only assigned once, which is
    # a requirement imposed on the intermediate code generation phase.
    replacements = {}
    for elem in input_elems:
        if isinstance(elem, CopyOperation):
            if isinstance(elem.target, SymbolOperand):
                if isinstance(elem.target.symbol, TemporarySymbol):
                    replacements[elem.target.symbol] = elem.operand

    # Now we make another pass over the list and rewrite the operations
    # to include the replacements.

    def replacement(operand):
        if isinstance(operand, SymbolOperand):
            if operand.symbol in replacements:
                return replacements[operand.symbol]
        return operand

    for elem in input_elems:
        # skip if this is a copy to a temporary we're replacing, since
        # we don't need that temporary anymore.
        if (
            isinstance(elem, CopyOperation) and
            isinstance(elem.target, SymbolOperand)
        ):
            if elem.target.symbol in replacements:
                continue

        elem.replace_operands(replacement)
        ret_elems.append(elem)

    # This doesn't currently remove *all* redundancy... in particular, it
    # won't catch this sort of structure:
    #   temp = op1 + op2
    #   named = temp
    # But we'll live with that for now and let it get taken care of by
    # later optimizations.

    return ret_elems


class IncompatibleTypesError(CompilerError):
    pass


class UnknownSymbolError(CompilerError):
    pass


class NotConstantError(CompilerError):
    pass


class InvalidLValueError(CompilerError):
    pass
