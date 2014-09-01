
import weakref
import collections
from alamatic.types import *


__all__ = [
    "TypeInferer",
]


class TypeInferer(object):

    def __init__(self):
        self._block_inferences = weakref.WeakKeyDictionary()

    def infer_types_for_block(self, block):
        old_inferences = self._block_inferences.get(block)
        inferences = TypeTable()
        for pred_block in block.predecessors:
            if pred_block in self._block_inferences:
                inferences.merge(self._block_inferences[pred_block])
            else:
                # Until our predecessors have run, just produce an empty
                # table signalling that all of our types are unknown.
                self._block_inferences[block] = TypeTable()
                # Tell the driver that we changed nothing so that we won't get
                # run again yet. This predecessor will eventually run and
                # produce a result and then we'll get re-queued.
                return False

        context = TypeContext(inferences)

        for instruction in block.operation_instructions:
            operation = instruction.operation
            target = instruction.target
            if hasattr(target, "symbol"):  # looks like a SymbolOperand
                inferences.add(
                    target.symbol,
                    operation.get_result_type(context),
                )

        self._block_inferences[block] = inferences
        return inferences != old_inferences

    def get_inferences_for_block(self, block):
        return self._block_inferences.get(block, TypeTable())


class TypeTable(object):

    def __init__(self):
        self._symbol_types = weakref.WeakKeyDictionary()
        self._equivalences = weakref.WeakKeyDictionary()

    def merge(self, other):
        for symbol, other_type in other._symbol_types.iteritems():
            self.add(symbol, other_type)

    def add(self, symbol, new_type):
        if symbol in self._symbol_types:
            existing_type = self[symbol]
            unified_type = existing_type.unify(
                new_type,
            )
            if unified_type is not existing_type:
                self._equivalences[existing_type] = unified_type
            if unified_type is not new_type:
                self._equivalences[new_type] = unified_type

            self._symbol_types[symbol] = unified_type
        else:
            self._symbol_types[symbol] = new_type

    def canonical_type(self, given_type):
        ret_type = given_type
        while ret_type in self._equivalences:
            ret_type = self._equivalences[ret_type]

        # Need to also recursively normalize the type's args, if any.
        canonical_args = tuple(
            self.canonical_type(x) for x in ret_type.type_args
        )
        if canonical_args != ret_type.type_args:
            ret_type = Type(
                ret_type.cons,
                canonical_args,
                ret_type.value_args,
            )

        # Tend towards a flat equivalence tree to simplify
        # future visits to the same types.
        if ret_type != given_type:
            self._equivalences[given_type] = ret_type

        return ret_type

    def __getitem__(self, key):
        if key not in self._symbol_types:
            ret_type = TypeConstructor().instantiate()
        else:
            ret_type = self.canonical_type(self._symbol_types[key])

        # Update in case we've changed the type during normalization,
        # so our normalization work is easier next time we visit this symbol.
        self._symbol_types[key] = ret_type

        return ret_type

    def __iter__(self):
        for symbol in self._symbol_types:
            yield symbol

    def itervalues(self):
        for symbol in self:
            yield self[symbol]

    def iteritems(self):
        for symbol in self:
            yield symbol, self[symbol]

    def __eq__(self, other):
        return self._symbol_types == other._symbol_types


class TypeContext(object):

    def __init__(self, type_table):
        self.type_table = type_table

    def operand_type(self, operand):
        return operand.get_type(self.type_table)

    def unknown(self):
        return get_fresh_type_variable()