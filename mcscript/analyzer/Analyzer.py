from typing import List, Optional, Tuple

from lark import Tree

from mcscript import Logger
from mcscript.analyzer.VariableContext import VariableAccess, VariableContext

NamespaceContext = List[VariableContext]


def getVar(contexts: List[NamespaceContext], name: str) -> Optional[VariableContext]:
    for context in reversed(contexts):
        for var in context:
            if var.identifier == name:
                return var
    return None


class Analyzer:
    """
    Analyzes variables in a mcscript syntax tree.
    Returns a list of lists of `VariableContext`
    Hooks:
        - declaration
        - static_declaration
        - index_setter?
        - term_ip
        - value
    """

    def __init__(self):
        self.state = []
        self.stack = []

    def pushContext(self):
        context = []
        self.state.append(context)
        self.stack.append(context)

    def popContext(self):
        self.stack.pop()

    def getCurrentIndex(self) -> int:
        return len(self.state) - 1

    def visit(self, tree: Tree):
        return getattr(self, tree.data, self._default)(tree)

    def _default(self, tree: Tree):
        return [self.visit(i) for i in tree.children if isinstance(i, Tree)]

    def analyze(self, tree: Tree) -> Tuple[Tree, List[NamespaceContext]]:
        """
        Analyzes the tree and returns information per context that were found per variable.

        Args:
            tree: The tree to analyze

        Returns:
            the original tree and a list of context which contain a list of `VariableContext`
        """
        self.state = []
        self.stack = []
        self.pushContext()

        self.visit(tree)

        return tree, self.state

    def block(self, tree: Tree):
        self.pushContext()
        [self.visit(i) for i in tree.children]
        self.popContext()

    def declaration(self, tree: Tree):
        accessor, expression = tree.children
        self.visit(expression)

        identifier, *not_implemented = accessor.children
        if not_implemented:
            return

        if var := getVar(self.stack, identifier):
            var.writes.append(VariableAccess(tree, self.getCurrentIndex()))
        else:
            self.stack[-1].append(VariableContext(
                identifier,
                VariableAccess(tree, self.getCurrentIndex()),
                False,
                False
            ))

    def static_declaration(self, tree: Tree):
        accessor, expression = tree.children[0].children
        self.visit(expression)

        identifier, *_ = accessor.children

        if var := getVar(self.stack, identifier):
            var.writes.append(VariableAccess(tree, self.getCurrentIndex()))
        else:
            self.stack[-1].append(VariableContext(
                identifier,
                VariableAccess(tree, self.getCurrentIndex()),
                True,
                False
            ))

    def term_ip(self, tree: Tree):
        accessor, operator, expression = tree.children
        self.visit(expression)

        identifier, *not_implemented = accessor.children
        if not_implemented:
            return

        if var := getVar(self.stack, identifier):
            var.writes.append(VariableAccess(tree, self.getCurrentIndex()))
        else:
            # otherwise the user tries to access an undefined variable
            Logger.error(f"[Analyzer] invalid variable access: '{identifier}' is not defined")

    def value(self, tree: Tree):
        value, = tree.children
        if isinstance(value, Tree) and value.data == "accessor":
            identifier, *not_implemented = value.children
            if not not_implemented:
                var = getVar(self.stack, identifier)
                if var:
                    var.reads.append(VariableAccess(tree, self.getCurrentIndex()))
        elif isinstance(value, Tree):
            for child in value.children:
                if isinstance(child, Tree):
                    self.visit(child)
