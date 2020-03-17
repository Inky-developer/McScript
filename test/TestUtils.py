import unittest

from src.mcscript.utils.utils import deprecated


class TestUtils(unittest.TestCase):
    def testDeprecated(self):
        @deprecated("Do not use this function")
        def test(a, b):
            return a * b

        self.assertEqual(test(2, 3), 6)
