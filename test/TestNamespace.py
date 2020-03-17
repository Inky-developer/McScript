import unittest

from src.mcscript.utils.NamespaceBase import NamespaceBase


class TestNamespace(unittest.TestCase):
    def setUp(self) -> None:
        sub = NamespaceBase(None, 0)
        sub.namespace["sub"] = "yes"
        self.namespace = NamespaceBase(sub, 1)
        self.namespace.namespace["a"] = "b"
        self.namespace.namespace["b"] = "a"

    def test_namespace(self):
        self.assertEqual(self.namespace["a"], "b")
        self.assertNotIn("d", self.namespace)
        self.assertIn("b", self.namespace)

    def test_full_namespace(self):
        self.assertEqual(self.namespace["sub"], "yes")
        self.assertTrue("sub" in self.namespace)

    def test_iterator(self):
        self.assertEqual(set(self.namespace), {"yes", "a", "b"})


if __name__ == '__main__':
    unittest.main()
