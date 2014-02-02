
from alamatic.util import overloadable
from alamatic.intermediate import *
from alamatic.types import Unknown
from alamatic.compilelogging import pos_link, CompilerError

from collections import defaultdict, deque


class DataState(object):

    def __init__(self):
        self._symbol_values = {}
        self.ready = False

    def update_from_predecessors(self, predecessor_states):
        symbols = set()
        for predecessor_state in predecessor_states:
            pass


def analyze_graph(graph):
    entry_block = graph.entry_block
    queue = deque([entry_block])
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
    return dict(data_states)


def _analyze_block(block, data_state):

    @overloadable
    def evaluate(operation):
        raise Exception(
            "evaluate not implemented for %r" % type(operation)
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

    # Evaluate for operands
    @evaluate.overload(ConstantOperand)
    def evaluate(operand):
        return operand.value

    @evaluate.overload(SymbolOperand)
    def evaluate(operand):
        return Unknown()

    changed = False

    for instruction in block.operation_instructions:
        operation = instruction.operation
        # FIXME: This won't converge for variables since they'll always
        # come back as unknown via evaluate. Need a different design.
        prev_result = evaluate(instruction.target)
        new_result = evaluate(operation, instruction.position)
        if type(new_result) is not type(prev_result):
            changed = True
            print "Type of %r changed to %r!" % (instruction.target, type(new_result))
        elif new_result.is_changed_from(prev_result):
            print "Value of %r changed to %r!" % (instruction.target, new_result)
            changed = True

    data_state.ready = True
    return not changed


class SymbolNotInitializedError(CompilerError):
    pass


class InappropriateTypeError(CompilerError):
    pass


class SymbolValueNotKnownError(CompilerError):
    pass
