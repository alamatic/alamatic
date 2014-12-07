
import unittest
from mock import MagicMock
from alamatic.llvmlowering.analyses import (
    AnalysisResult,
    Initialization,
    Poison,
)


class TestAnalysisResult(unittest.TestCase):

    def test_init(self):
        mock_function = MagicMock()
        dummy_variable = None
        mock_function.local_variables = [
            dummy_variable, dummy_variable, dummy_variable,
        ]
        mock_function.register_count = 4
        dummy_globals = []
        dummy_constants = []

        result = AnalysisResult(
            function=mock_function,
            global_inits=dummy_globals,
            constant_inits=dummy_constants,
        )

        self.assertEqual(
            result.local_inits,
            [
                None, None, None,
            ],
        )
        self.assertEqual(
            result.register_inits,
            [
                None, None, None, None,
            ],
        )
        self.assertTrue(result.global_inits is dummy_globals)
        self.assertTrue(result.constant_inits is dummy_constants)

    def test_call(self):
        mock_caller = MagicMock()
        mock_caller.local_variables = [None, None]
        mock_caller.register_count = 3

        mock_type = MagicMock()

        class DummyValue(object):
            def __init__(self, type, data):
                self.data = data
                self.type = type

            def __repr__(self):
                return repr(self.data)

            def __eq__(self, other):
                return self.type is other.type and self.data == other.data

        def di(value, type=mock_type):
            mock_value = DummyValue(type, value)
            return Initialization(mock_value)

        dummy_globals = [
            None,
            di(2),
            di(3),
        ]
        dummy_constants = [
            None,
            di(5),
            di(6),
        ]

        caller_result = AnalysisResult(
            function=mock_caller,
            global_inits=dummy_globals,
            constant_inits=dummy_constants,
        )

        mock_callee = MagicMock()
        mock_callee.local_variables = [None]
        mock_callee.register_count = 2
        callee_result = caller_result.prepare_for_call(mock_callee)

        self.assertEqual(
            caller_result.global_inits,
            callee_result.global_inits,
        )
        self.assertEqual(
            caller_result.constant_inits,
            callee_result.constant_inits,
        )
        self.assertEqual(
            caller_result.local_inits,
            [None, None],
        )
        self.assertEqual(
            callee_result.local_inits,
            [None],
        )
        self.assertEqual(
            caller_result.register_inits,
            [None, None, None],
        )
        self.assertEqual(
            callee_result.register_inits,
            [None, None],
        )

        callee_result.global_inits[0] = di(10)
        callee_result.global_inits[1] = di(20)
        callee_result.constant_inits[0] = di(40)
        callee_result.constant_inits[1] = di(50)

        self.assertEqual(
            [
                x.value.data if x else None
                for x in caller_result.global_inits
            ],
            [None, 2, 3],
        )
        self.assertEqual(
            [
                x.value.data if x else None
                for x in caller_result.constant_inits
            ],
            [None, 5, 6],
        )

        caller_result.merge_from_call(callee_result)
        self.assertEqual(
            caller_result.global_inits,
            [
                di(10),
                di(2),
                di(3),
            ],
        )
        self.assertEqual(
            caller_result.constant_inits,
            [
                di(40),
                Initialization(Poison),
                di(6),
            ],
        )
