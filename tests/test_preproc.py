
import unittest
import mock
from collections import defaultdict
from alamatic.preprocessor import (
    _preprocess_cfg,
)


class Logger(object):

    def __init__(self):
        self.visited = []

    def stream(self, marker, visits_per_block=1):
        visits = defaultdict(lambda: visits_per_block)

        def log(block):
            self.visited.append(
                (marker, block),
            )
            visits[block] = visits[block] - 1
            return visits[block] > 0

        return log


class TestPreprocess(unittest.TestCase):

    def test_simple(self):
        graph = mock.MagicMock('graph')
        entry_block = mock.MagicMock('entry_block')
        middle_block = mock.MagicMock('middle_block')
        exit_block = mock.MagicMock('exit_block')
        graph.blocks = (
            entry_block,
            middle_block,
            exit_block,
        )
        entry_block.successors = set([middle_block])
        middle_block.successors = set([exit_block])
        exit_block.successors = set([])

        logger = Logger()

        _preprocess_cfg(
            graph,
            [
                logger.stream('a'),
                logger.stream('b'),
            ]
        )

        self.assertEqual(
            logger.visited,
            [
                ('a', entry_block),
                ('b', entry_block),
                ('a', middle_block),
                ('b', middle_block),
                ('a', exit_block),
                ('b', exit_block),
            ],
        )

    # FIXME: Test some more complex cases, like diamonds, loops,
    # and iterations where we actually change something.
