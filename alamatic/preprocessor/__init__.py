
from collections import deque
from alamatic.preprocessor.deadcode import *


def preprocess_cfg(graph):
    preprocessors = []

    ## Dead Code Removal Phases
    # Optimize conditional terminators with constant operands
    preprocessors.append(optimize_terminator)

    _preprocess_cfg(graph, preprocessors)


def _preprocess_cfg(graph, preprocessors):
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

    while len(queue) > 0:
        current_block = queue.popleft()
        queue_successors = False
        run_again = True
        while run_again:
            run_again = False
            for preprocessor in preprocessors:
                changed = preprocessor(current_block)
                if changed:
                    run_again = True
                    queue_successors = True

        if queue_successors:
            # FIXME: This might put the same block in the queue
            # twice, if there's a cycle or diamond on the graph,
            # causing a redundant visit in some cases.
            queue.extend(current_block.successors)
