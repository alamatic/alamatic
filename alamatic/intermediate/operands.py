
class Operand(object):
    @property
    def can_be_lvalue(self):
        return False


class Temporary(Operand):
    def __init__(self, index, source_range=None):
        self.index = index
        self.source_range = source_range

    @property
    def can_be_lvalue(self):
        return True


class LiteralValue(Operand):

    def __init__(self, value, source_range=None):
        self.value = value
        self.source_range = source_range



class NamedConstant(Operand):
    pass


class GlobalVariablePointer(Operand):
    pass
