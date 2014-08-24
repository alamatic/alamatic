
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
        )) + " : " + repr(self.source_range) + ")"

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


class SymbolOperand(Operand):
    # both lvalue and rvalue
    def __init__(self, symbol, source_range=None):
        self.symbol = symbol
        self.source_range = source_range

    @property
    def params(self):
        yield self.symbol


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
