
class Operation(object):

    def __repr__(self):
        params = tuple(self.params)
        return "<alamatic.intermediate.%s%r>" % (type(self).__name__, params)

    def get_result_type(self, context):
        # FIXME: Once the others are all implemented, it should be a
        # fatal error not to have a get_result_type implementation.
        return context.unknown()


class CopyOperation(Operation):

    def __init__(self, operand):
        self.operand = operand

    @property
    def params(self):
        yield self.operand

    def replace_operands(self, replace):
        self.operand = replace(self.operand)

    def get_result_type(self, context):
        return context.operand_type(self.operand)


class UnaryOperation(Operation):

    def __init__(self, operator, operand):
        self.operator = operator
        self.operand = operand

    def replace_operands(self, replace):
        self.target = replace(self.target)
        self.operand = replace(self.operand)


class BinaryOperation(Operation):
    def __init__(self, lhs, operator, rhs):
        self.lhs = lhs
        self.operator = operator
        self.rhs = rhs

    @property
    def params(self):
        yield self.lhs
        yield self.operator
        yield self.rhs

    def replace_operands(self, replace):
        self.lhs = replace(self.lhs)
        self.rhs = replace(self.rhs)


class CallOperation(Operation):
    def __init__(self, callee, args, kwargs):
        self.callee = callee
        self.args = args
        self.kwargs = kwargs

    @property
    def params(self):
        yield self.callee
        yield self.args
        yield self.kwargs

    def replace_operands(self, replace):
        self.callee = replace(self.callee)
        for i, arg in enumerate(self.args):
            self.args[i] = replace(self.args[i])
        for k, arg in self.kwargs.iteritems():
            self.kwargs[k] = replace(self.kwargs[k])


class AttributeLookupOperation(Operation):
    def __init__(self, operand, name):
        self.operand = operand
        self.name = name

    def replace_operands(self, replace):
        self.operand = replace(self.operand)


class IndexOperation(Operation):
    def __init__(self, operand, index):
        self.operand = operand
        self.index = index

    def replace_operands(self, replace):
        self.operand = replace(self.operand)


class SliceOperation(Operation):
    def __init__(self, operand, start_index, length):
        self.operand = operand
        self.start_index = start_index
        self.length = length

    def replace_operands(self, replace):
        self.operand = replace(self.operand)
