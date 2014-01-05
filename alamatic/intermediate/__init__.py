
from alamatic.compilelogging import CompilerError, pos_link
from alamatic.intermediate.symbols import *
from alamatic.intermediate.instructions import *
from alamatic.intermediate.operations import *
from alamatic.intermediate.operands import *
from alamatic.intermediate.base import *


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
    replaceable = lambda elem: (
        isinstance(elem, OperationInstruction) and
        isinstance(elem.operation, CopyOperation) and
        isinstance(elem.target, SymbolOperand) and
        isinstance(elem.target.symbol, TemporarySymbol)
    )
    for elem in input_elems:
        if replaceable(elem):
            replacements[elem.target.symbol] = elem.operation.operand

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
        if replaceable(elem):
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
