
from alamatic.intermediate import *
from alamatic.util import overloadable

from collections import deque


__all__ = [
    'execute_unit',
]


def execute_unit(unit, args=None, parent_frame=None, call_position=None):
    from alamatic.preprocessor.datastate import CallFrame
    frame = CallFrame(
        unit,
        call_position=call_position,
        parent=parent_frame,
    )
    return UnitExecutor.execute(unit, frame)


class UnitExecutor(object):

    @classmethod
    def execute(cls, unit, frame):
        self = cls()
        self.unit = unit
        self.frame = frame
        self._execute()

    def _execute(self):
        from alamatic.preprocessor.datastate import DataState

        unit = self.unit
        graph = self.unit.graph
        frame = self.frame

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
                data_states[current_block] = DataState(frame)

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
            # it's unreachable code and so we don't need to consider it
            # anymore.
            if current_block is not entry_block:
                if len(current_block.predecessors) == 0:
                    # FIXME: We should also update the block to have no
                    # successors so that it's completely disconnected from
                    # the rest of the graph and so won't turn up in a later
                    # traversal.
                    continue

            current_data_state = data_states[current_block]
            current_data_state.update_from_predecessors(
                (
                    data_states[pred_block]
                    for pred_block in current_block.predecessors
                )
            )

            changed = BlockExecutor.execute(
                current_block,
                current_data_state,
                unit,
                frame,
            )
            changed = self._analyze_block(current_block, current_data_state)

            if changed or not current_data_state.ready:
                # (Re-)visit all of this block's successors before we
                # do any more work.
                for next_block in current_block.successors:
                    if next_block not in blocks_in_queue:
                        queue.appendleft(next_block)
                        blocks_in_queue.add(next_block)

        self.exit_state = data_states[graph.exit_block]

    def _analyze_block(self, block, data_state):

        any_changed = False


class BlockExecutor(object):

    @classmethod
    def execute(cls, block, state, unit, frame):
        self = cls()
        self.block = block
        self.state = state
        self.unit = unit
        self.frame = frame
        self.changed = False
        self._execute()
        return self.changed

    def _execute(self):
        block = self.block
        state = self.state

        any_changed = False

        for instruction in block.operation_instructions:
            operation = instruction.operation
            result = self.evaluate(
                operation,
                instruction.position,
            )
            this_changed = self.assign(
                instruction.target,
                result,
                position=instruction.position,
            )
            if this_changed:
                any_changed = True

        self.changed = any_changed

    # Applies to both operations and rvalue operands
    @overloadable
    def evaluate(self, what, position=None):
        raise Exception(
            "evaluate not implemented for %r" % type(what)
        )

    # Applies only to lvalue operands
    @overloadable
    def assign(self, operand, value, position=None):
        raise Exception(
            "assign not implemented for %r" % type(operand)
        )

    ### Evaluate implementations for operations

    @evaluate.overload(CopyOperation)
    def evaluate(self, operation, position=None):
        return self.evaluate(operation.operand)

    @evaluate.overload(CallOperation)
    def evaluate(self, operation, position=None):
        callee = self.evaluate(operation.callee)
        impl_type = callee.apparent_type
        return impl_type.call(
            operation.callee,
            operation.args,
            position=position,
        )

    @evaluate.overload(BinaryOperation)
    def evaluate(self, operation, position=None):
        lhs = self.evaluate(operation.lhs)
        rhs = self.evaluate(operation.rhs)
        impl_type = lhs.apparent_type
        return getattr(impl_type, operation.operator)(
            lhs, rhs, position=position,
        )

    ### Evaluate implementations for operands
    # These don't take a position because the operands themselves
    # have position members built in.

    @evaluate.overload(ConstantOperand)
    def evaluate(self, operand):
        return operand.value

    @evaluate.overload(SymbolOperand)
    def evaluate(self, operand):
        return self.state.retrieve_symbol_value(
            operand.symbol,
            position=operand.position,
        )

    ### Assign implementations for operands

    @assign.overload(SymbolOperand)
    def assign(self, operand, value, position=None):
        return self.state.assign_symbol_value(
            operand.symbol,
            value,
            position=position,
        )
