
from alamatic.util import overloadable
from alamatic.intermediate import *
from alamatic.types import Unknown
from alamatic.compilelogging import pos_link, CompilerError

from collections import defaultdict, deque


class DataState(object):

    def __init__(self):
        # FIXME: Doing this based on symbols is not a correct design because
        # the same symbol can refer to multiple locations in different
        # contexts e.g. if a function is called recursively.
        # Instead there should be an indirection where each call frame
        # establishes which memory object each symbol refers to
        # and the data state then works in terms of this "memory object"
        # concept rather than the symbols directly.
        # This would also be the appropriate layer to introduce the concept
        # of "lifetimes" that allow us to distinguish between globals and
        # locals, so we can e.g. forbid returning a reference to a local
        # variable, and also give us a way to represent memory objects
        # that are only indirectly related to symbols, such a referents,
        # array members and object attributes.
        self._symbol_values = {}
        self.ready = False

    def update_from_predecessors(self, predecessor_states):
        symbols = set()
        for predecessor_state in predecessor_states:
            pass

    def assign(self, symbol, value, position=None):
        # FIXME: Need to do checks in here to make sure the type isn't
        # changing after the first known initialization.
        old_value = self._symbol_values.get(symbol, Unknown())
        self._symbol_values[symbol] = value
        return (
            type(old_value) is not type(value) or
            value.is_changed_from(old_value)
        )

    def retrieve(self, symbol, value, position=None):
        try:
            result = self._symbol_values[symbol]
        except KeyError:
            if self.ready:
                raise SymbolNotInitializedError(
                    symbol.user_friendly_name,
                    " may not be initialized at ",
                    pos_link(position),
                )
            else:
                return Unknown()

        if isinstance(symbol, NamedSymbol) and not symbol.const:
            # We pretend we don't know the value of a variable even if
            # we do happen to know it, since this prevents us from optimizing
            # away branches that depend on variables before we've had a
            # chance to check them for validity. These might still get
            # optimized away in later phases, but this phase is about type
            # inference and constant resolution, not about optimization.
            return Unknown(result.apparent_type)
        else:
            return result


def analyze_graph(graph):
    entry_block = graph.entry_block
    queue = deque(list(graph.blocks))
    data_states = {}
    blocks_in_queue = set(queue)
    while True:
        try:
            current_block = queue.popleft()
        except IndexError:
            # Queue depleted, so stop.
            break

        if current_block not in data_states:
            data_states[current_block] = DataState()

        do_instead = [
            pred_block for pred_block in current_block.predecessors
            if pred_block not in data_states
        ]
        if len(do_instead) > 0:
            # Try this one again once its predecessors are dealt with.
            queue.appendleft(current_block)

            # Queue all the predecessors.
            for next_block in do_instead:
                if next_block in blocks_in_queue:
                    # Will move the existing element to top of queue
                    queue.remove(next_block)
                else:
                    blocks_in_queue.add(next_block)

                queue.appendleft(next_block)

            continue

        # If we got this far then the current block is no longer in the
        # queue, so we should update our set.
        blocks_in_queue.remove(current_block)

        # If analysis has removed all predecessors from this block then
        # it's unreachable code and so we don't need to consider it anymore.
        if current_block is not entry_block:
            if len(current_block.predecessors) == 0:
                # FIXME: We should also update the block to have no successors
                # so that it's completely disconnected from the rest of the
                # graph and so won't turn up in a later traversal.
                continue

        current_data_state = data_states[current_block]
        current_data_state.update_from_predecessors(
            (
                data_states[pred_block]
                for pred_block in current_block.predecessors
            )
        )

        changed = _analyze_block(current_block, current_data_state)

        if changed:
            # (Re-)visit all of this block's successors before we
            # do any more work.
            for next_block in current_block.successors:
                if next_block not in blocks_in_queue:
                    queue.appendleft(next_block)
                    blocks_in_queue.add(next_block)

    # Eventually we'll return some sort of analysis object here.
    return {
        k: v._symbol_values for k, v in data_states.iteritems()
    }


def _analyze_block(block, data_state):

    # Applies to both operations and rvalue operands
    @overloadable
    def evaluate(what):
        raise Exception(
            "evaluate not implemented for %r" % type(what)
        )

    # Applies only to lvalue operands
    @overloadable
    def assign(operand):
        raise Exception(
            "assign not implemented for %r" % type(operand)
        )

    # Evaluate for operations
    @evaluate.overload(CopyOperation)
    def evaluate(operation, position):
        return evaluate(operation.operand)

    @evaluate.overload(CallOperation)
    def evaluate(operation, position):
        callee = evaluate(operation.callee)
        impl_type = callee.apparent_type
        return impl_type.call(
            operation.callee,
            operation.args,
            position=position,
        )

    @evaluate.overload(BinaryOperation)
    def evaluate(operation, position):
        lhs = evaluate(operation.lhs)
        rhs = evaluate(operation.rhs)
        impl_type = lhs.apparent_type
        return getattr(impl_type, operation.operator)(
            lhs, rhs, position,
        )

    # Evaluate for rvalue operands
    @evaluate.overload(ConstantOperand)
    def evaluate(operand):
        return operand.value

    @evaluate.overload(SymbolOperand)
    def evaluate(operand):
        return Unknown()

    # Assign for lvalue operands
    @assign.overload(SymbolOperand)
    def assign(operand, value):
        symbol = operand.symbol
        return data_state.assign(symbol, value)

    any_changed = False

    for instruction in block.operation_instructions:
        operation = instruction.operation
        result = evaluate(operation, instruction.position)
        this_changed = assign(instruction.target, result)
        if this_changed:
            any_changed = True

    data_state.ready = True
    return any_changed


class SymbolNotInitializedError(CompilerError):
    pass


class InappropriateTypeError(CompilerError):
    pass


class SymbolValueNotKnownError(CompilerError):
    pass
