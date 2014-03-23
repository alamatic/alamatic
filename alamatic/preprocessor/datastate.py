

class Lifetime(object):

    def __init__(self, parent=None):
        self.parent = parent

    def allocate_cell(self):
        return Cell(self)

    def outlives(self, other_lifetime):
        current = other_lifetime.parent
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
        self.lifetime = lifetime
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

    def get_symbol_values(self, state):
        ret = {}
        for symbol in self.symbol_cells:
            ret[symbol] = state.retrieve_symbol_value
        return ret


class Cell(object):
    def __init__(self, lifetime):
        self.lifetime = lifetime

    def outlives(self, other_cell):
        return self.lifetime.outlives(other_cell.lifetime)


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
        from alamatic.types import Unknown

        # Ensure we have an actual list of states so we can iterate
        # it multiple times.
        pred_states = list(pred_states)

        all_preds_ready = True
        for pred_state in pred_states:
            if not pred_state.ready:
                all_preds_ready = False
                break

        self.ready = True

        if all_preds_ready:
            # Merge all of the predecessor values to produce our
            # entry state.
            all_cells = set()
            for pred_state in pred_states:
                all_cells.update(pred_state._cell_values.iterkeys())

            for cell in all_cells:
                merged_value = None
                for pred_state in pred_states:
                    try:
                        this_value = pred_state._cell_values[cell]
                    except KeyError:
                        # This state has no knowledge of the given cell,
                        # so skip.
                        continue

                    if merged_value is None:
                        merged_value = this_value
                    else:
                        merged_value = merged_value.merge(this_value)

                self._cell_values[cell] = merged_value

        else:
            for pred_state in pred_states:
                for cell in pred_state._cell_values:
                    self._cell_values[cell] = Unknown()

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
            return Unknown()

        if symbol.assignable:
            # If a symbol is assignable (meaning it can change at runtime)
            # then we pretend we don't know the value of it, even if
            # we do happen to know it. This prevents us from optimizing
            # away branches that depend on variables before we've had a
            # chance to check them for validity. These might still get
            # optimized away in later phases, but this phase is about type
            # inference and constant resolution, not about optimization.
            return Unknown(result.apparent_type)
        else:
            return result
