import unittest
from textwrap import dedent

from mcscript.data.templates.DataReader import DataReader


# noinspection SpellCheckingInspection
class TestDataReader(unittest.TestCase):
    def setUp(self) -> None:
        self.reader = DataReader()

    def test_success(self):
        success = dedent("""
        [A]
        B

        [C]
        D

        [longKey]
        longValue
        [E]
        F
        """)
        successDict = {"A": ["B"], "C": ["D"], "longKey": ["longValue"], "E": ["F"]}
        self.assertEqual(self.reader.read(success), successDict)

        success = dedent("""
        [Key]
        value
        value2
        """)
        successDict = {"Key": ["value\nvalue2"]}
        self.assertEqual(self.reader.read(success), successDict)

    def testFail(self):
        fail = dedent("""
        Value
        [Key]
        """)
        self.assertRaises(ValueError, self.reader.read, fail)

        fail = dedent("""
        [InvalidKey]aszhf
        value
        """)
        self.assertRaises(ValueError, self.reader.read, fail)
