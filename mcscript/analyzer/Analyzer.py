from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from lark import Tree, Token

from mcscript import Logger
from mcscript.analyzer.VariableContext import VariableAccess, VariableContext

NamespaceContext = List[VariableContext]


@dataclass()
class ContextData:
    line: int
    column: int
    context: NamespaceContext

    def append(self, context: VariableContext):
        self.context.append(context)


def getVar(contexts: List[ContextData], name: str) -> Optional[VariableContext]:
    for context in reversed(contexts):
        for var in context.context:
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
        - function parameters
    """

    def __init__(self):
        # A context is identified by its line and column
        self.contexts: List[ContextData] = []
        self.stack: List[ContextData] = []

    def push_context(self, line: int, column: int):
        self.contexts.append(ContextData(line, column, []))
        self.stack.append(self.contexts[-1])

    def pop_context(self):
        self.stack.pop()

    def visit(self, tree: Tree):
        return getattr(self, tree.data, self._default)(tree)

    def _default(self, tree: Tree):
        return [self.visit(i) for i in tree.children if isinstance(i, Tree)]

    def analyze(self, tree: Tree) -> Tuple[Tree, Dict[Tuple[int, int], NamespaceContext]]:
        """
        Analyzes the tree and returns information per context that were found per variable.

        Args:
            tree: The tree to analyze

        Returns:
            the original tree and a list of context which contain a list of `VariableContext`
        """
        self.contexts = []
        # the global context
        self.push_context(0, 0)

        self.visit(tree)

        return tree, {(i.line, i.column): i.context for i in self.contexts}

    def block(self, tree: Tree):
        self.push_context(tree.line, tree.column)
        [self.visit(i) for i in tree.children]
        self.pop_context()

    def struct_block(self, tree: Tree):
        self.push_context(tree.line, tree.column)
        [self.visit(i) for i in tree.children]
        self.pop_context()

    def function_definition(self, tree: Tree):
        _, _name, parameter_list, _return_type, body = tree.children
        self.push_context(body.line, body.column)
        self_type, *parameters = parameter_list.children

        if self_type:
            self.stack[-1].append(VariableContext(
                self_type,
                VariableAccess(self_type, (self.stack[-1].line, self.stack[-1].column)),
                False,
                False
            ))

        [self.visit(i) for i in parameters]
        [self.visit(i) for i in body.children]
        self.pop_context()

    def function_parameter(self, tree: Tree):
        name, _type = tree.children
        self.stack[-1].append(VariableContext(
            name,
            VariableAccess(tree, (self.stack[-1].line, self.stack[-1].column)),
            False,
            False
        ))

    def control_for(self, tree: Tree):
        _, var, _, expression, block = tree.children
        self.push_context(block.line, block.column)
        self.stack[-1].append(VariableContext(
            var,
            VariableAccess(var, (self.stack[-1].line, self.stack[-1].column)),
            False,
            False
        ))
        self.visit(expression)
        [self.visit(i) for i in block.children]
        self.pop_context()

    def declaration(self, tree: Tree):
        accessor, expression = tree.children
        self.visit(expression)

        # for now, treat every property of an object as the object itself
        identifier, *_ignore_children = accessor.children

        self._handle_variable(identifier, tree)

    def multi_declaration(self, tree: Tree):
        *values, expression = tree.children
        self.visit(expression)

        for value in values:
            value, *_ignore_children = value.children
            self._handle_variable(value, tree)

    def static_declaration(self, tree: Tree):
        accessor, expression = tree.children[0].children
        self.visit(expression)

        identifier, *_ = accessor.children

        self._handle_variable(identifier, tree)

    def term_ip(self, tree: Tree):
        accessor, operator, expression = tree.children
        self.visit(expression)

        identifier, *_ = accessor.children

        if var := getVar(self.stack, identifier):
            var.writes.append(VariableAccess(tree, (self.stack[-1].line, self.stack[-1].column)))
        else:
            # otherwise the user tries to access an undefined variable
            Logger.error(f"[Analyzer] invalid variable access: '{identifier}' is not defined")

    def index_setter(self, tree: Tree):
        accessor, index, expression = tree.children
        self.visit(expression)

        identifier, *not_implemented = accessor.children
        if not_implemented:
            return

        if var := getVar(self.stack, identifier):
            var.writes.append(VariableAccess(tree, (self.stack[-1].line, self.stack[-1].column)))
        else:
            Logger.error(f"[Analyzer] invalid variable array setter: '{identifier}' is not defined")

    def value(self, tree: Tree):
        value, = tree.children

        # simply extract the accessor part
        if isinstance(value, Tree) and value.data == "array_accessor":
            value = value.children[0]

        if isinstance(value, Tree) and value.data == "accessor":
            identifier, *not_implemented = value.children
            if not not_implemented:
                var = getVar(self.stack, identifier)
                if var:
                    var.reads.append(VariableAccess(tree, (self.stack[-1].line, self.stack[-1].column)))
        elif isinstance(value, Tree) and value.data == "function_call":
            accessor, *arguments = value.children
            base_obj, *children = accessor.children
            if children:
                self._handle_variable(base_obj, value)
        elif isinstance(value, Tree):
            for child in value.children:
                if isinstance(child, Tree):
                    self.visit(child)

    #########################
    # Utility functions #####
    #########################
    def _handle_variable(self, variable_name: Token, declaration: Tree):
        if var := getVar(self.stack, variable_name):
            var.writes.append(VariableAccess(declaration, (self.stack[-1].line, self.stack[-1].column)))
        else:
            self.stack[-1].append(VariableContext(
                variable_name,
                VariableAccess(declaration, (self.stack[-1].line, self.stack[-1].column)),
                False,
                False
            ))
