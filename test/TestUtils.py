import unittest

from src.mcscript.utils.utils import deprecated, run_function_once


class TestUtils(unittest.TestCase):
    def testDeprecated(self):
        @deprecated("Do not use this function")
        def test(a, b):
            return a * b

        self.assertEqual(test(2, 3), 6)

    def testRunOnce(self):
        n = 0

        @run_function_once
        def increment_n():
            nonlocal n
            n += 1

        self.assertEqual(n, 0)
        increment_n()
        self.assertEqual(n, 1)
        increment_n()
        self.assertEqual(n, 1)
