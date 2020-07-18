from __future__ import annotations

from contextlib import contextmanager
from typing import Callable, Dict, List, Optional, Tuple, Union

from lark import Tree

from mcscript.analyzer.Analyzer import NamespaceContext
from mcscript.compiler.CompilerConstants import CompilerConstants
from mcscript.compiler.Context import Context
from mcscript.compiler.ContextStack import ContextStack
from mcscript.compiler.ContextType import ContextType
from mcscript.data.Config import Config
from mcscript.ir.IrMaster import IrMaster
from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.utils.Datapack import Datapack
from mcscript.utils.Scoreboard import Scoreboard
from mcscript.utils.addressCounter import ScoreboardAddressCounter, AddressCounter
from mcscript.utils.resources import DataPath, ScoreboardValue, Identifier, ResourceSpecifier


class CompileState:
    """
    This class keeps track of the current state of the compilation
    """

    def __init__(self, code: str, contexts: Dict[Tuple[int, int], NamespaceContext], compileFunction: Callable,
                 config: Config):
        self.compileFunction = compileFunction

        self.code = code.split("\n")
        self.currentTree: Optional[Tree] = None

        self.config = config
        self.datapack = Datapack(config)

        self.scoreboards: List[Scoreboard] = [
            Scoreboard(self.config.get_scoreboard("main"), True, 0),
            Scoreboard("entities", False, 1)
        ]

        self.scoreboard_main = self.scoreboards[0]
        self.data_path_main = DataPath(self.config.storage_id, self.config.get_storage("vars").split("."))

        self.compilerConstants = CompilerConstants(self.scoreboard_main)

        # ToDo: maybe move to ir gen code?
        self.node_block_counter = AddressCounter("block_{}_")

        # ToDO: add (line, column) class
        self.contexts = contexts
        self.stack: ContextStack = ContextStack()
        # self.stack.append(Namespace(0, namespaceType=NamespaceType.GLOBAL))
        self.stack.append(Context(0, None, ContextType.GLOBAL, [], self.scoreboard_main, self.data_path_main))

        # the ir master class
        self.ir = IrMaster()

    def get_nbt_address(self, name: str) -> NbtAddressResource:
        """
        formats the variable name so that it can be used as an nbt name

        Args:
            name: the name

        Returns:
            A nbt address
        """
        return NbtAddressResource(self.currentContext().nbt_format.format(name))

    def getConstant(self, constant: int) -> ScoreboardValue:
        """ Wrapper for compilerConstant"""
        return ScoreboardValue(Identifier(self.compilerConstants.get_constant(constant)), self.scoreboard_main),

    @property
    def expressionStack(self) -> ScoreboardAddressCounter:
        """
        shortcut for currentNamespace().expressionStack
        Used by a lot of old code.
        """
        return self.currentContext().scoreboard_formatter

    def load(self, value: Resource) -> Resource:
        """
        tries to load the resource and returns the result.

        Parameters:
            value: the value

        Returns:
            the value itself or an addressResource
        """
        if isinstance(value, Tree):
            return self.load(self.compileFunction(value))
        # ToDO: check if new class needs special treatment
        # if isinstance(value, ConditionalExecute):
        #     return value.toResource(self)
        try:
            return value.load(self)
        except TypeError:
            raise ValueError(
                f"Cannot load resource of type {type(value)}. It cannot be converted to a Number.")

    def toResource(self, value: Union[Resource, Tree]) -> Resource:
        """
        Converts a value to a resource. similar to ´load´ but does not actually load the resource.

        Args:
            value: the value

        Returns:
            a Resource
        """
        from mcscript.lang.builtins.builtins import BuiltinFunction

        # ToDo: Make BuiltinFunction a resource
        if isinstance(value, (Resource, BuiltinFunction)):
            return value
        # # the condition tree evaluates to a conditional execute. Convert to a boolean here
        # if isinstance(value, ConditionalExecute):
        #     return value.toResource(self)
        return self.toResource(self.compileFunction(value))

    # def toCondition(self, value: Tree) -> ConditionalExecute:
    #     """
    #     Converts the tree to a conditional execute
    #
    #     Args:
    #         value: the tree
    #
    #     Returns:
    #         the condition
    #     """
    #     result = self.compileFunction(value)
    #
    #     if isinstance(result, ConditionalExecute):
    #         return result
    #     elif isinstance(result, Resource):
    #         result = result.convertToBoolean(self)
    #         if result.isStatic:
    #             return ConditionalExecute(result.value == 1)
    #         return ConditionalExecute(Command.EXECUTE(
    #             sub=ExecuteCommand.IF_SCORE_RANGE(
    #                 stack=result.value,
    #                 range=1
    #             )
    #         ))
    #     raise ValueError(f"Unknown type {result}")

    def currentContext(self) -> Context:
        return self.stack.tail()

    def popContext(self):
        self.stack.pop()

    def pushContext(self, contextType: ContextType, line: int, column: int) -> Context:
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
        self.stack.append(context)
        return context

    @contextmanager
    def node_block(self, context_type: ContextType, line: int, column: int):
        """
        Creates a new context and a new ir function.
        Yields the name of the block

        Args:
            context_type: the type of context
            line: the line
            column: the column
        """
        self.pushContext(context_type, line, column)
        block_name = self.node_block_counter.next()

        with self.ir.with_function(block_name):
            try:
                yield block_name
            finally:
                self.popContext()

    def getDebugLines(self, a, _):
        return self.code[a - 1].strip()

    def scoreboard_value(self, identifier: str) -> ScoreboardValue:
        return ScoreboardValue(Identifier(identifier), self.scoreboard_main)

    def resource_specifier_main(self, name: str) -> ResourceSpecifier:
        return ResourceSpecifier(self.config.NAME, name)
