
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

    @property
    def constant_value(self):
        from alamatic.intermediate import Unknown
        return Unknown

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

    @property
    def constant_value(self):
        return self.value

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
