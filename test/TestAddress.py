import unittest

from src.mcscript.utils.Address import Address


class TestAddress(unittest.TestCase):
    def testAddress(self):
        a = Address(".{}")

        self.assertEqual(a.next().embed(), ".0")
        self.assertEqual(a.next().embed(), ".1")
        self.assertEqual(a.getValue().embed(), ".2")
        self.assertEqual(a.previous().embed(), ".1")
        self.assertEqual(a.previous().embed(), ".0")
        self.assertRaises(ValueError, a.previous)
