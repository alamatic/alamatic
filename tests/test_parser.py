
import unittest
from alamatic.compiler import CompileState
from alamatic.compilelogging import ERROR
from alamatic.parser import *
from StringIO import StringIO


class TestParser(unittest.TestCase):

    def test_basics(self):

        # Empty module
        state = CompileState()
        module = parse_module(
            state,
            StringIO(""),
            "foo",
            "foo.ala",
        )
        self.assertEqual(module.name, "foo")
        self.assertEqual(module.position, ("foo.ala", 1, 0))
        self.assertEqual(module.stmts, [])

        # Module with two simple statements
        state = CompileState()
        module = parse_module(
            state,
            StringIO("foo = 1\n\nfoo = 2"),
            "foo",
            "foo.ala",
        )
        self.assertEqual(len(module.stmts), 2)
