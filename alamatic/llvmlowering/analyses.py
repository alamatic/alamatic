
import alamatic.diagnostics as diag
from alamatic.types import Poison

from collections import deque


class Initialization(object):

    def __init__(self, value, source_range=None):
        self.value = value
        self.source_range = source_range

    def __repr__(self):
        return "<Initialization %r at %s>" % (self.value, self.source_range)

    def __eq__(self, other):
        if type(self) is not type(other):
            return NotImplemented

        return (
            self.value == other.value and
            self.source_range == other.source_range
        )

    def __ne__(self, other):
        return not self == other


class AnalysisResult(object):

    def __init__(
        self,
        function,
        global_inits,
        constant_inits
    ):
        self.function = function
        self.global_inits = global_inits
        self.local_inits = [None for x in function.local_variables]
        self.diagnostics = []
        self.constant_inits = constant_inits
        self.register_inits = [None] * function.register_count

    @property
    def equality_test_key(self):
        return (
            self.function,
            self.global_inits,
            self.local_inits,
            self.constant_inits,
            self.register_inits,
        )

    def __cmp__(self, other):
        if not isinstance(other, AnalysisResult):
            return -1
        return cmp(self.equality_test_key, other.equality_test_key)

    def merge_from_call(self, result):
        """
        Given an analysis result from a call, merge in any mutations to
        the global variable and constant initializations.
        """
        for idx, init in enumerate(result.constant_inits):
            if self.constant_inits[idx] is None:
                self.constant_inits[idx] = init
            else:
                if self.constant_inits[idx].value is Poison:
                    continue

                previous_init = self.constant_inits[idx]
                if previous_init.value != init.value:
                    self.add_diagnostic(
                        diag.ConstantMultipleInitialization(
                            # TODO: Figure out how to get at the symbol
                            # name in here.
                            symbol_name='TODO',
                            init_1_range=previous_init.source_range,
                            init_2_range=init.source_range,
                        )
                    )
                    self.constant_inits[idx] = Initialization(Poison)
                else:
                    # Just keep the value we had, since values are equal.
                    pass

        for idx, init in enumerate(result.global_inits):
            if self.global_inits[idx] is None:
                self.global_inits[idx] = init
            else:
                if self.global_inits[idx].value is Poison:
                    continue

                previous_init = self.global_inits[idx]
                if previous_init.value.type is not init.value.type:
                    self.add_diagnostic(
                        diag.ConstantMultipleInitialization(
                            # TODO: Figure out how to get at the symbol
                            # name in here.
                            symbol_name='TODO',
                            init_1_range=previous_init.source_range,
                            init_2_range=init.source_range,
                        )
                    )

                    self.global_inits[idx] = Initialization(Poison)
                else:
                    # Just keep the value we had, since types are equal.
                    pass

    def prepare_for_call(self, callee):
        """
        Create an initial analysis result for a call from the current
        context to some other function.

        The new analysis result inherits a snapshot of the global variable and
        constant initializations from this context but gets a fresh set
        of local variable and register initializations.

        Once the child function analysis is complete the final analysis
        result can be merged back in with :py:meth:`merge_from_call`.
        """
        # Clone the global and constant initializations so the child
        # can safely mutate them. We'll merge them back in later in
        # merge_child_from_call.
        global_inits = list(self.global_inits)
        constant_inits = list(self.constant_inits)
        return AnalysisResult(callee, global_inits, constant_inits)

    def prepare_for_successor(self, results):
        """
        Create an initial analysis result for analyzing a basic block that
        is preceeded by other blocks whose final analyses are given in
        ``results``.

        When given multiple successor results, the initializations are
        merged and, when conflicts arise, error diagnostics are added and
        the initializations are replaced with poisoned initializations.
        """
        results = list(results)
        if len(results) == 0:
            raise Exception("Can't merge empty set of analysis results")

        function = self.function
        global_inits = [None for x in self.global_inits]
        constant_inits = [None for x in self.constant_inits]
        new = type(self)(function, global_inits, constant_inits)

        diagnostics = new.diagnostics
        for result in results:
            if result is None:
                # We have a not-yet-processed result in our set, so
                # we'll just return a conservative "everything unknown"
                # result for now, allowing us to converge on a complete
                # analysis iteratively.
                # (This result may have some inherited diagnostics in it,
                # but we'll ignore them since they aren't used during
                # analysis and will get refreshed when we revisit this
                # incomplete analysis later.)
                return new

            diagnostics.extend(result.diagnostics)

        for result in results:
            for idx, init in enumerate(result.register_inits):
                if new.register_inits[idx] is not None:
                    # This should never happen as long as the AST lowering
                    # is behaving itself.
                    raise Exception(
                        "Multiple initializations for register %03x" % idx
                    )

                if result.register_inits[idx] is not None:
                    new.register_inits[idx] = result.register_inits[idx]

            for idx, init in enumerate(result.constant_inits):
                if new.constant_inits[idx] is None:
                    new.constant_inits[idx] = init
                else:
                    if new.constant_inits[idx].value is Poison:
                        continue

                    previous_init = new.constant_inits[idx]
                    new.add_diagnostic(
                        diag.ConstantMultipleInitialization(
                            # TODO: Figure out how to get at the symbol
                            # name in here.
                            symbol_name='TODO',
                            init_1_range=previous_init.source_range,
                            init_2_range=init.source_range,
                        )
                    )

                    new.constant_inits[idx] = Initialization(Poison)

            for idx, init in enumerate(result.global_inits):
                if new.global_inits[idx] is not None:
                    previous_type = new.global_inits[idx].value.type
                    new_type = init.value.type

                    if previous_type is not new_type:
                        new.add_diagnostic(
                            diag.SymbolTypeMismatch(
                                # TODO: Figure out how to get at the symbol
                                # name in here.
                                symbol_name='TODO',
                                type_1=previous_type,
                                type_1_range=(
                                    new.global_inits[idx].source_range
                                ),
                                type_2=new_type,
                                type_2_range=(
                                    init.source_range
                                ),
                            )
                        )
                        new.global_inits[idx] = Initialization(Poison)
                        continue
                    else:
                        # We'll just arbitrarily keep the earlier
                        # initialization, which will usually be from
                        # earlier in the source code.
                        continue
                else:
                    new.global_inits[idx] = init

        return new

    def add_diagnostic(self, diagnostic):
        self.diagnostics.append(diagnostic)


def analyze_function(function, initial_result):
    graph = function.graph
    blocks = list(graph.blocks)

    # For each block we've processed, this is its analysis result.
    # None for blocks we've not yet processed.
    block_results = {}

    # The possible predecessors of each block. To start with this includes
    # all possible predecessors, but edges will be eliminated as we discover
    # conditional branches with constant predicates that allow us to mark
    # certain clusters as unreachable.
    block_predecessors = {}

    # As we discover conditional branches with constant predicates we will
    # start to eliminate clusters from this set, allowing us to consider
    # only the reachable blocks.
    blocks_reachable = set(blocks)

    graph = function.graph

    # Initialize our per-block state structures.
    for block in graph.blocks:
        block_results[block] = None
        if block not in block_predecessors:
            block_predecessors[block] = set()

        for successor_block in block.terminator.successor_blocks:
            if successor_block not in block_predecessors:
                block_predecessors[successor_block] = set()

            block_predecessors[successor_block].add(block)

    queue = deque(graph.blocks)

    while len(queue) > 0:
        current_block = queue.popleft()

        queue_successors = set()
        run_again = True
        while run_again:
            run_again = False
            previous_result = block_results[current_block]
            if len(block_predecessors[current_block]):
                new_result = initial_result.prepare_for_successor(
                    block_results[x] for x in block_predecessors[current_block]
                )
            else:
                new_result = initial_result.prepare_for_successor(
                    [initial_result],
                )
            new_result, successors = analyze_basic_block(
                current_block, new_result,
            )

            # Update our predecessor edges and reachable set based on
            # the successor set we've produced during analysis.
            # This is where we'll eliminate blocks that are proven to
            # be unreachable.
            possibly_dead_successors = (
                set(current_block.terminator.successor_blocks) - successors
            ) & blocks_reachable

            kill_unreachable_blocks(
                possibly_dead_successors,
                block_predecessors,
                blocks_reachable,
            )

            assert isinstance(new_result, AnalysisResult)
            if new_result != previous_result:
                # Keep analyzing until we converge on a stable state.
                run_again = True
                queue_successors = successors

            block_results[current_block] = new_result

        # FIXME: This might put the same block in the queue twice, if
        # there's a cycle or diamond in the graph, causing a redundant
        # visit in some cases.
        queue.extend(queue_successors)

    return block_results[graph.exit_block]


def analyze_basic_block(block, initial_result):
    return (initial_result, set())


def kill_unreachable_blocks(
    candidate_blocks,
    block_predecessors,
    blocks_reachable,
):
    """
    Takes a set of candidate blocks and marks them as unreachable if
    they only have one reachable predecessor remaining.

    After doing so, transitively visits the successors of any killed blocks
    and possibly kills them too, if they are now in turn unreachable.
    """

    for block in candidate_blocks:
        predecessors = block_predecessors[block]
        predecessors &= blocks_reachable
        if len(predecessors) < 2:
            maybe_dead = (
                set(block.terminator.successor_blocks) & blocks_reachable
            )
            blocks_reachable.remove(block)

            if len(maybe_dead) > 0:
                kill_unreachable_blocks(
                    maybe_dead,
                    block_predecessors,
                    blocks_reachable,
                )
