
from alamatic.context import context


class Operand(object):
    source_range = None

    def __init__(self, source_range=None):
        self.source_range = source_range

    @property
    def params(self):
        return []

    def __str__(self):
        return type(self).__name__ + "(" + (', '.join(
            (str(x) for x in self.params)
        )) + " : " + str(self.source_range.start) + ")"

    def __repr__(self):
        return "<alamatic.intermediate.%s>" % self.__str__()

    @property
    def constant_value(self):
        from alamatic.intermediate import Unknown
        return Unknown


class ConstantOperand(Operand):
    # rvalue only
    def __init__(self, value, source_range=None):
        self.value = value
        self.source_range = source_range

    @property
    def params(self):
        yield self.value

    @property
    def constant_value(self):
        return self.value

    @property
    def type(self):
        from alamatic.types import get_type_for_constant
        return get_type_for_constant(self.value)

    def build_llvm_value(self, builder):
        return self.type.impl.get_llvm_constant(self.value)


class SymbolOperand(Operand):
    # both lvalue and rvalue
    def __init__(self, symbol, source_range=None):
        self.symbol = symbol
        self.source_range = source_range

    @property
    def params(self):
        yield self.symbol

    @property
    def constant_value(self):
        if self.symbol in context.symbol_constant_values:
            return context.symbol_constant_values[self.symbol]
        else:
            from alamatic.intermediate import Unknown
            return Unknown

    @property
    def type(self):
        return self.symbol.type

    def build_llvm_value(self, builder):
        if self.symbol.is_temporary:
            # Easy! We can just return its value directly, since it's
            # already a register.
            return context.symbol_llvm_values[self.symbol]
        else:
            # Otherwise what we have is actually a pointer to memory,
            # so we need to load it first.
            return builder.instrs.load(
                context.symbol_llvm_values[self.symbol],
            )

    def build_llvm_store_ptr(self, builder):
        if self.symbol.is_temporary:
            return None
        else:
            return context.symbol_llvm_values[self.symbol]


class IndexOperand(Operand):
    # lvalue only
    def __init__(self, source, index, source_range=None):
        self.source = source
        self.index = index
        self.source_range = source_range


class AttributeOperand(Operand):
    # lvalue only
    def __init__(self, source, name, source_range=None):
        self.source = source
        self.name = name
        self.source_range = source_range


class DereferenceOperand(Operand):
    # lvalue only
    def __init__(self, source, source_range=None):
        self.source = source
        self.source_range = source_range
