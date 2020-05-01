from contextlib import contextmanager
from typing import Callable, List, Optional, Union

from lark import Tree

from mcscript.analyzer.Analyzer import NamespaceContext
from mcscript.compiler.CompilerConstants import CompilerConstants
from mcscript.compiler.Namespace import Namespace, NamespaceType
from mcscript.compiler.NamespaceStack import NamespaceStack
from mcscript.data.Config import Config
from mcscript.data.Scoreboard import Scoreboard
from mcscript.data.commands import Command, ConditionalExecute, ExecuteCommand
from mcscript.lang.resource.AddressResource import AddressResource
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.utils.Address import Address
from mcscript.utils.Datapack import Datapack


class CompileState:
    """
    This class keeps track of the current state of the compilation
    """

    def __init__(self, code: str, contexts: List[NamespaceContext], compileFunction: Callable, config: Config):
        self.compileFunction = compileFunction

        self.code = code.split("\n")
        self.currentTree: Optional[Tree] = None

        self.config = config
        self.datapack = Datapack(config)

        self.codeBlockStack = Address("block_{}")
        # ToDo the two stacks below should not be in state.vars
        # ToDo make temporaryStorageStack NbtAddress
        self.temporaryStorageStack = Address("_temp.tmp{}")
        self.selectorCounter = 1

        self.scoreboards: List[Scoreboard] = [
            Scoreboard(self.config.get_scoreboard("main"), True, 0),
            Scoreboard("entities", False, 1)
        ]
        self.compilerConstants = CompilerConstants()

        self.contexts = contexts
        self.stack: NamespaceStack = NamespaceStack()
        self.stack.append(Namespace(0, namespaceType=NamespaceType.GLOBAL))

        self.fileStructure = self.datapack.getMainDirectory().getPath("functions").fileStructure
        self.lineCount = 0

        # used in combination with the context manager to determine whether the changes should be kepts
        self._commit = False

    def getConstant(self, constant: int) -> AddressResource:
        """ Wrapper for compilerConstant"""
        return AddressResource(self.compilerConstants.getConstant(constant), True)

    @property
    def expressionStack(self):
        """
        shortcut for expressionStack.currentNamespace().expressionStack.
        Used by a lot of old code.
        """
        return self.currentNamespace().expressionStack

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
        if isinstance(value, ConditionalExecute):
            return value.toResource(self)
        try:
            return value.load(self)
        except TypeError:
            raise ValueError(
                f"Cannot load resource of type {type(value)}. It cannot be converted to a Number.")

    def toResource(self, value: Union[Resource, ConditionalExecute, Tree]) -> Resource:
        """
        Converts a value to a resource. similar to ´load´ but does not actually load the resource.

        Args:
            value: the value

        Returns:
            a Resource
        """
        if isinstance(value, Resource):
            return value
        # the condition tree evaluates to a conditional execute. Convert to a boolean here
        if isinstance(value, ConditionalExecute):
            return value.toResource(self)
        return self.toResource(self.compileFunction(value))

    def toCondition(self, value: Tree) -> ConditionalExecute:
        """
        Converts the tree to a conditional execute

        Args:
            value: the tree

        Returns:
            the condition
        """
        result = self.compileFunction(value)

        if isinstance(result, ConditionalExecute):
            return result
        elif isinstance(result, Resource):
            result = result.convertToBoolean(self)
            if result.isStatic:
                return ConditionalExecute(result.value == 1)
            return ConditionalExecute(Command.EXECUTE(
                sub=ExecuteCommand.IF_SCORE_RANGE(
                    stack=result.value,
                    range=1
                )
            ))
        raise ValueError(f"Unknown type {result}")

    def pushBlock(self, blockName: str = None, namespaceType: NamespaceType = NamespaceType.BLOCK) -> AddressResource:
        """ creates a new file and namespace and returns the block id."""
        blockName = blockName or self.codeBlockStack.next()
        self.fileStructure.pushFile(blockName)
        self.pushStack(namespaceType)
        return blockName

    def popBlock(self):
        self.popStack()
        self.fileStructure.popFile()

    def commit(self):
        self._commit = True

    @contextmanager
    def push(self):
        """
        Pushes a new file to `self.fileStructure`.
        At exit, copies the contents of the file to the previous file if `commit` was called
        """
        self._commit = False
        self.fileStructure.pushFile("__tmp__", save=False)
        try:
            yield
        finally:
            if self._commit:
                file = self.fileStructure.get()
                file.seek(0)
                contents = file.read()
                self.fileStructure.popFile()

                self.write(contents)
            else:
                self.fileStructure.popFile()

    @property
    def nextNamespaceDefaults(self):
        return self._nextNamespaceDefaults

    @nextNamespaceDefaults.setter
    def nextNamespaceDefaults(self, value: List[str]):
        self._nextNamespaceDefaults = value

    def write(self, string: str):
        self.lineCount += string.count("\n")
        self.fileStructure.get().write(string)

    def writeline(self, string: str = ""):
        self.write(string)
        self.write("\n")

    def currentNamespace(self) -> Namespace:
        return self.stack.tail()

    def popStack(self):
        self.stack.pop()

    def pushStack(self, namespaceType: NamespaceType):
        namespace = Namespace(self.stack.index(), namespaceType, self.currentNamespace())
        self.stack.append(namespace)
        return namespace

    def getDebugLines(self, a, _):
        return self.code[a - 1].strip()
