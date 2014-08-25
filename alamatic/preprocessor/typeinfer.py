
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

        # TODO: Actually do some type inference.

        self._block_inferences[block] = inferences
        return False

    def get_inferences_for_block(self, block):
        return self._block_inferences.get(block, TypeTable())


class TypeTable(object):

    def __init__(self):
        self._symbol_types = collections.defaultdict(
            lambda x: TypeConstructor().instantiate()
        )

    def merge(self, other):
        for symbol, other_type in other._symbol_types.iteritems():
            self.add(symbol, other_type)

    def add(self, symbol, new_type):
        if symbol in self._symbol_types:
            existing_type = self[symbol]
            unified_type = existing_type.unify(
                new_type,
            )
            self._symbol_types[symbol] = unified_type
        else:
            self._symbol_types[symbol] = new_type

    def __getitem__(self, key):
        return self._symbol_types[key]

    def __eq__(self, other):
        return self._symbol_types == other._symbol_types
