

class Lifetime(object):

    def __init__(self, parent=None):
        pass

    def allocate_cell(self):
        return Cell(self)

    def outlives(self, other_lifetime):
        current = other_lifetime
        while current is not None:
            if current is self:
                return True
            current = current.parent
        return False

    @property
    def root(self):
        current = self
        while current.parent is not None:
            current = current.parent
        return current


class CallFrame(object):

    def __init__(self, unit, call_position=None, parent=None):
        lifetime = Lifetime(
            parent.lifetime if parent is not None else None
        )
        self.call_position = call_position
        self.unit = unit
        self.parent = parent
        symbol_cells = {}
        for symbol in unit.symbols.all_symbols:
            symbol_cells[symbol] = lifetime.allocate_cell()
        self.symbol_cells = symbol_cells

    def get_cell_for_symbol(self, symbol):
        current = self
        while current is not None:
            if symbol in current.symbol_cells:
                return current.symbol_cells[symbol]
            current = current.parent

        # Should never happen if the intermediate code generator
        # behaves correctly.
        raise Exception(
            "No cell is allocated for symbol %r" % symbol
        )


class Cell(object):
    def __init__(self, lifetime):
        self.lifetime = lifetime

    def outlives(self, other_cell):
        self.lifetime.outlives(other_cell.lifetime)


class DataState(object):

    def __init__(self, frame):
        self.frame = frame
        self._cell_values = {}
        self._cell_init_positions = {}
        # A data state starts off in a "not ready" state, which means it
        # doesn't yet have all of the information from the predecessor states
        # and so it should avoid raising noisy errors when things don't
        # look correct. Once the predecessor states are all ready we will
        # start looking for errors and converge on a stable set of values
        # and types if no errors are encountered along the way.
        self.ready = False

    def update_from_predecessors(self, pred_states):
        all_preds_ready = True
        for pred_state in pred_states:
            if not pred_state.ready:
                all_preds_ready = False
                break

        # TODO:
        #  - If any predecessor states are not yet ready, initialize
        #    all inherited cells as unknown.
        #  - If all predecessor states are ready, replace our cell values
        #    table with a merge of all of the predecessor values.
        #  - If two predecessors give us differing types for a particular
        #    cell, then that's an inconsistent initialization error.

        if all_preds_ready:
            self.ready = True

    def assign_symbol_value(self, symbol, value, position=None):
        from alamatic.types import Unknown
        from alamatic.preprocessor import InappropriateTypeError
        from alamatic.compilelogging import pos_link

        cell = self.frame.get_cell_for_symbol(symbol)
        old_value = self._cell_values.get(cell, Unknown())

        if old_value.apparent_type is Unknown:
            self._cell_init_positions[cell] = position
        else:
            if old_value.apparent_type is not value.apparent_type:
                raise InappropriateTypeError(
                    "Can't assign ", value.apparent_type.__name__,
                    " to ", symbol.user_friendly_name,
                    " at ", pos_link(position),
                    " because it was initialized as ",
                    old_value.apparent_type.__name__,
                    " at ", pos_link(self._cell_init_positions[cell]),
                    frame=self.frame,
                )

        self._cell_values[cell] = value
        return (
            type(old_value) is not type(value) or
            value.is_changed_from(old_value)
        )

    def retrieve_symbol_value(self, symbol, position=None):
        from alamatic.types import Unknown
        from alamatic.compilelogging import pos_link
        from alamatic.intermediate import (
            NamedSymbol,
        )
        from alamatic.preprocessor.errors import (
            SymbolNotInitializedError,
        )
        cell = self.frame.get_cell_for_symbol(symbol)
        try:
            result = self._cell_values[cell]
        except KeyError:
            if self.ready:
                raise SymbolNotInitializedError(
                    symbol.user_friendly_name,
                    " is not definitely initialized at ",
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
