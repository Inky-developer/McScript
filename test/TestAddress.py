import unittest

from mcscript.utils.addressCounter import ScoreboardAddressCounter


class TestAddress(unittest.TestCase):
    def testAddress(self):
        a = ScoreboardAddressCounter(".{}")

        self.assertEqual(a.next().embed(), ".0")
        self.assertEqual(a.next().embed(), ".1")
        self.assertEqual(a.getValue().embed(), ".2")
        self.assertEqual(a.previous().embed(), ".1")
        self.assertEqual(a.previous().embed(), ".0")
        self.assertRaises(ValueError, a.previous)
