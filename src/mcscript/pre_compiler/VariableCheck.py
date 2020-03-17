from locale import str
from typing import Dict, Tuple

from lark import Visitor, Tree

from src.mcscript.data import defaultCode


class VariableCheck(Visitor):
    """
    checks all variables if they are determined at all time
    ToDo: partially determined variables
    Currently returns always False
    """

    def __init__(self):
        self.namespace: Dict[str, bool] = {}

    def check(self, tree) -> Tuple[Tree, Dict[str, bool]]:
        self.namespace = {}
        self.visit(tree)
        return tree, self.namespace

    def control_while(self, tree):
        for iterable in (tree.find_data("declaration"), tree.find_data("term_ip")):
            for subTree in iterable:
                varName, *_ = subTree.children
                self.namespace[varName] = False

        return tree

    def function_definition(self, tree):
        name, parameter, block = tree.children
        if name in defaultCode.MAGIC_FUNCTIONS:
            for iterable in (tree.find_data("declaration"), tree.find_data("term_ip")):
                for subTree in iterable:
                    varName, *_ = subTree.children
                    self.namespace[varName] = False

    def declaration(self, tree):
        name, value = tree.children
        # self.namespace[name] = (
        #     value.isDetermined and
        #     self.namespace.get(name, True)
        # )
        self.namespace[name] = False
        return tree
