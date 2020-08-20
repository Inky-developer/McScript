from __future__ import annotations

from contextlib import contextmanager
from typing import Callable, Dict, Optional, Tuple, Union, ContextManager, Set, List

from lark import Tree

from mcscript.analyzer.Analyzer import NamespaceContext
from mcscript.compiler.Context import Context
from mcscript.compiler.ContextStack import ContextStack
from mcscript.compiler.ContextType import ContextType
from mcscript.data.Config import Config
from mcscript.ir.IrMaster import IrMaster
from mcscript.ir.command_components import ScoreRange
from mcscript.ir.components import FunctionNode, ConditionalNode
from mcscript.lang.Type import Type
from mcscript.lang.resource import BooleanResource
from mcscript.lang.resource.BooleanResource import BooleanResource
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.resource.base.functionSignature import FunctionSignature
from mcscript.utils.Scoreboard import Scoreboard
from mcscript.utils.addressCounter import ScoreboardAddressCounter, AddressCounter, StorageAddressCounter
from mcscript.utils.resources import DataPath, ScoreboardValue, Identifier, ResourceSpecifier


class CompileState:
    """
    This class keeps track of the current state of the compilation
    """

    def __init__(self, code: str, contexts: Dict[Tuple[int, int], NamespaceContext], compile_function: Callable,
                 config: Config):
        self._compile_function = compile_function

        self.code = code.split("\n")
        self._currentTree: Optional[Tree] = None

        self.config = config

        # each custom type gets a unique id. Atomic types have negative uids starting at -1
        # NEVER remove anything from this since the len is used to generate uids.
        self.custom_types: Dict[str, Type] = {}

        self.scoreboard_main = Scoreboard(self.config.get_scoreboard("main"), True, 0)

        self.data_path_main = DataPath(self.config.storage_id, self.config.get_storage("stack").split("."))
        self.data_path_temp = DataPath(self.config.storage_id, self.config.get_storage("temp").split("."))

        # ToDo: maybe move to ir gen code?
        self.node_block_counter = AddressCounter("block_{}_")
        self.temp_data_counter = StorageAddressCounter(self.data_path_temp)

        # ToDO: add (line, column) class
        self.contexts = contexts
        self.stack: ContextStack = ContextStack()
        # self.stack.append(Namespace(0, namespaceType=NamespaceType.GLOBAL))
        self.stack.append(Context(0, None, ContextType.GLOBAL, NamespaceContext([], [], (0, 0)), self.scoreboard_main,
                                  self.data_path_main))
        # keeps track of all functions that are right now called
        self.function_call_stack: List[FunctionSignature] = []

        # the ir master class
        self.ir = IrMaster()

        self.ir.scoreboards = [
            self.scoreboard_main
        ]

    def compile_ast(self, tree: Tree):
        self._compile_function(tree)

    @property
    def currentTree(self) -> Optional[Tree]:
        return self._currentTree

    @currentTree.setter
    def currentTree(self, value: Tree):
        self._currentTree = value
        if value is None:
            return

    @contextmanager
    def with_function(self, signature: FunctionSignature):
        self.function_call_stack.append(signature)
        try:
            yield
        finally:
            self.function_call_stack.pop()

    def new_type(self, name: str, bases: Set[Type]) -> Type:
        t = Type(len(self.custom_types), name, bases)
        self.custom_types[t.name] = t
        return t

    def get_nbt_address(self, name: str) -> DataPath:
        """
        formats the variable name so that it can be used as an nbt name

        Args:
            name: the name

        Returns:
            A nbt address
        """
        return self.currentContext().nbt_format.format(name)

    @property
    def expressionStack(self) -> ScoreboardAddressCounter:
        """
        shortcut for currentNamespace().expressionStack
        Used by a lot of old code.
        """
        return self.currentContext().scoreboard_formatter

    def toResource(self, value: Union[Resource, Tree]) -> Resource:
        """
        Converts a value to a resource. similar to ´load´ but does not actually load the resource.

        Args:
            value: the value

        Returns:
            a Resource
        """
        if isinstance(value, Tree):
            return self.toResource(self._compile_function(value))
        if not isinstance(value, Resource):
            raise ValueError(f"Expected a resource, but got '{value}'")
        return value

    def to_condition(self, value: Union[Resource, Tree]) -> ConditionalNode:
        """
        Converts the value to a ConditionalNode in a more efficient way

        Args:
            value: the value

        Returns:
            a ConditionalNode
        """
        if isinstance(value, Tree):
            with self.currentContext().set_global_state("condition", True):
                value = self._compile_function(value)
            return self.to_condition(value)
        if isinstance(value, BooleanResource):
            if value.is_static:
                return ConditionalNode([ConditionalNode.IfBool(bool(value.static_value))])

            return ConditionalNode([ConditionalNode.IfScoreMatches(value.scoreboard_value, ScoreRange(0), True)])
        if not isinstance(value, ConditionalNode):
            raise ValueError(f"Unexpected type {value}")
        return value

    def currentContext(self) -> Context:
        return self.stack.tail()

    def pop_context(self):
        self.stack.pop()

    def push_context(self, contextType: ContextType, line: int, column: int) -> Context:
        """
        Creates a new context and pushes it on the stack.
        Line and column are used to associate the variable context data.

        Args:
            contextType: The type of the context
            line: The line of the definition
            column: The column of the definition

        Returns:
            The new context
        """

        context = Context(self.stack.index(), (line, column), contextType, self.contexts[line, column],
                          self.scoreboard_main, self.data_path_main, self.stack.tail())
        context.update_static_resources(self)
        self.stack.append(context)
        return context

    @contextmanager
    def node_block(self, context_type: ContextType, line: int, column: int, block_name: str = None) \
            -> ContextManager[FunctionNode]:
        """
        Creates a new context and a new ir function.
        Yields the name of the block as a resource specifier

        Args:
            context_type: the type of context
            line: the line
            column: the column
            block_name: If specified the name for this block
        """
        self.push_context(context_type, line, column)
        block_name = block_name if block_name is not None else self.node_block_counter.next()

        with self.ir.with_function(self.resource_specifier_main(block_name)) as function:
            try:
                yield function
            finally:
                self.pop_context()

    def getDebugLines(self, a, _):
        return self.code[a - 1].strip()

    def scoreboard_value(self, identifier: str) -> ScoreboardValue:
        return ScoreboardValue(Identifier(identifier), self.scoreboard_main)

    def resource_specifier_main(self, name: str) -> ResourceSpecifier:
        return self.config.resource_specifier_main(name)
