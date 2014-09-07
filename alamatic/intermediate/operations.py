
from alamatic.util import QuickObject
from alamatic.intermediate import Unknown


class Operation(object):

    def __repr__(self):
        params = tuple(self.params)
        return "<alamatic.intermediate.%s%r>" % (type(self).__name__, params)

    @property
    def result_type(self):
        raise Exception(
            "result_type not implemented for %r" % self
        )


class CopyOperation(Operation):

    def __init__(self, operand):
        self.operand = operand

    @property
    def params(self):
        yield self.operand

    def replace_operands(self, replace):
        self.operand = replace(self.operand)

    @property
    def result_type(self):
        return self.operand.type

    def build_llvm_value(self, builder):
        return self.operand.build_llvm_value(builder)


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

    def _get_implementation(self):
        # TODO: Implement reverse-fallback behavior, allowing an
        # inverse operation to be used if rhs implements it.
        return getattr(self.lhs.type.impl, self.operator, None)

    @property
    def result_type(self):
        if self.lhs.type.is_variable or self.rhs.type.is_variable:
            return Unknown

        impl = self._get_implementation()

        if impl is None:
            # TODO: Signal an error in this case, since the operator
            # is not supported.
            return self.lhs.type

        # FIXME: Should pass in the source range for error reporting,
        # but currently operations don't have access to it.
        return impl.get_result_type(self.lhs, self.rhs)

    def build_llvm_value(self, builder):
        impl = self._get_implementation()

        return impl.build_llvm_value(builder, self.lhs, self.rhs)


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

    def _get_implementation(self):
        return getattr(self.callee.type.impl, "call", None)

    @property
    def result_type(self):
        if self.callee.type.is_variable:
            return Unknown

        impl = self._get_implementation()

        if impl is None:
            # TODO: Signal a "not callable" error in this case.
            return Unknown

        return impl.get_result_type(self.callee, self.args, self.kwargs)

    def build_llvm_value(self, builder):
        impl = self._get_implementation()

        return impl.build_llvm_value(
            builder, self.callee, self.args, self.kwargs,
        )


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
