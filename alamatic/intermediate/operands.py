
class Operand(object):
    @property
    def can_be_lvalue(self):
        return False


class Temporary(Operand):
    @property
    def can_be_lvalue(self):
        return True


class LiteralValue(Operand):
    pass


class GlobalConstant(Operand):
    pass


class TemplateConstant(Operand):
    pass


class GlobalVariablePointer(Operand):
    pass
