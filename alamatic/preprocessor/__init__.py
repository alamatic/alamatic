
from collections import deque
import contextlib

from alamatic.preprocessor.deadcode import *
from alamatic.preprocessor.typeinfer import *
from alamatic.context import new_context


def preprocess_cfg(graph):
    preprocessors = []

    type_inferer = TypeInferer()

    ## Dead Code Removal Phases
    # Optimize conditional terminators with constant operands
    preprocessors.append(optimize_terminator)

    ## Type Inference Phase
    preprocessors.append(type_inferer.infer_types_for_block)

    @contextlib.contextmanager
    def make_context(block):
        with new_context(
            symbol_types=type_inferer.get_inferences_for_block(
                block,
            ),
            symbol_constant_values={},
        ):
            yield

    _preprocess_cfg(graph, preprocessors, make_context)
    return PreprocessorResult(
        graph=graph,
        symbol_types=type_inferer.get_inferences_for_block(graph.exit_block),
        symbol_constant_values={},
    )


def _preprocess_cfg(graph, preprocessors, make_context):
    # This is really just a straightforward forward analysis driver,
    # visiting each basic block at least once and possibly visiting
    # some more than once if loops are present.
    # For each visit it iterates repeatedly over all of the
    # provided preprocessors until it manages to complete a pass
    # without changing anything. (Changes are signalled by the preprocessor
    # function returning True.)
    # Each time any of the preprocessors indicates a change for a block,
    # all of that block's successors are queued for a (re-)visit.
    # This is expected to eventually converge, once we've done all of
    # the processing we can possibly do. However, the graph is not
    # guaranteed to be valid and thus needs to be independently checked
    # for type consistency and other sorts of validity.

    queue = deque(graph.blocks)

    # Assume a worst-case runtime of O(n^2) where n is the number
    # of blocks. If we don't terminate by then we'll generate
    # a warning assuming that there's a bug preventing termination.
    warning_threshold = len(queue) * len(queue) * len(preprocessors)
    iterations = 0

    while len(queue) > 0:
        current_block = queue.popleft()

        queue_successors = False
        run_again = True
        while run_again:
            run_again = False
            for preprocessor in preprocessors:
                with make_context(current_block):
                    changed = preprocessor(current_block)
                if changed:
                    run_again = True
                    queue_successors = True

            iterations += 1
            if iterations == warning_threshold:
                # FIXME: Best do this some way other than printing in here.
                print "Warning: Preprocessor has done %i iterations on %r" % (
                    iterations,
                    graph,
                )

        if queue_successors:
            # FIXME: This might put the same block in the queue
            # twice, if there's a cycle or diamond on the graph,
            # causing a redundant visit in some cases.
            queue.extend(current_block.successors)


class PreprocessorResult(object):

    def __init__(
        self,
        graph,
        symbol_types,
        symbol_constant_values,
    ):
        self.graph = graph
        self.symbol_types = symbol_types
        self.symbol_constant_values = symbol_constant_values

    @contextlib.contextmanager
    def context(self):
        from alamatic.context import new_context
        with new_context(
            symbol_types=self.symbol_types,
            symbol_constant_values=self.symbol_constant_values,
        ):
            yield
