from typing import Callable, List, Optional

from lark import Tree

from mcscript.compiler.CompilerConstants import CompilerConstants
from mcscript.compiler.Namespace import Namespace, NamespaceType
from mcscript.data.Config import Config
from mcscript.lang.resource.AddressResource import AddressResource
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.utils.Address import Address
from mcscript.utils.Datapack import Datapack


class CompileState:
    """
    This class keeps track of the current state of the compilation
    """

    def __init__(self, code: str, compileFunction: Callable, config: Config):
        self.compileFunction = compileFunction

        self.code = code.split("\n")
        self.currentTree: Optional[Tree] = None

        self.config = config
        self.datapack = Datapack(config)

        self.codeBlockStack = Address("block_{}")
        self.temporaryStorageStack = Address("temp.tmp{}")
        self.compilerConstants = CompilerConstants()

        self.stack: List[Namespace] = [Namespace(0, namespaceType=NamespaceType.GLOBAL)]
        self._namespaceId = 1

        self.namespaceTotal = 1

        self.fileStructure = self.datapack.getMainDirectory().getPath("functions").fileStructure
        self.lineCount = 0

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
        try:
            return value.load(self)
        except TypeError:
            raise ValueError(
                f"Cannot load resource of type {type(value)}. It cannot be converted to a Number.")

    def toResource(self, value: Resource) -> Resource:
        """
        Converts a value to a resource. similar to ´load´ but does not actually load the resource.

        Args:
            value: the value

        Returns:
            a Resource
        """
        if isinstance(value, Resource):
            return value
        return self.toResource(self.compileFunction(value))

    def pushBlock(self, blockName: str = None, namespaceType: NamespaceType = NamespaceType.BLOCK) -> AddressResource:
        """ creates a new file and namespace and returns the block id."""
        blockName = blockName or self.codeBlockStack.next()
        self.fileStructure.pushFile(blockName)
        self.pushStack(namespaceType)
        return blockName

    def popBlock(self):
        self.popStack()
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
        return self.stack[-1]

    def popStack(self):
        self.stack.pop()

    def pushStack(self, namespaceType: NamespaceType):
        index = self._namespaceId
        self._namespaceId += 1 if namespaceType not in (namespaceType.LOOP, namespaceType.INLINE_FUNCTION) else 0
        namespace = Namespace(index, self.currentNamespace(), namespaceType)
        self.stack.append(namespace)
        return namespace

    def getDebugLines(self, a, _):
        return self.code[a - 1].strip()
