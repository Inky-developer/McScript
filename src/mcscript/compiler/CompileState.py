from typing import List, Callable

from lark import Tree

from src.mcscript.compiler.Namespace import Namespace
from src.mcscript.compiler.NamespaceType import NamespaceType
from src.mcscript.data.Config import Config
from src.mcscript.lang.resource.AddressResource import AddressResource
from src.mcscript.lang.resource.base.ResourceBase import Resource
from src.mcscript.utils.Address import Address
from src.mcscript.utils.Datapack import Datapack
from src.mcscript.utils.FileStructure import FileStructure


class CompileState:
    def __init__(self, code: str, compileFunction: Callable, config: Config):
        self.compileFunction = compileFunction
        self.code = code.split("\n")
        self.config = config
        self.datapack = Datapack(config)

        self.expressionStack = Address(".exp{}")
        self.codeBlockStack = Address("block_{}")
        self.temporaryStorageStack = Address("temp.tmp{}")

        self.stack: List[Namespace] = [Namespace(namespaceType=NamespaceType.GLOBAL)]
        self.namespaceTotal = 1

        self.fileStructure = self.datapack.getMainDirectory().getPath("functions").fileStructure
        self.lineCount = 0

    def load(self, value: Resource) -> Resource:
        """
        tries to load the resource and returns the result.
        :param value: the value
        :return: the value itself or an addressResource
        """
        if isinstance(value, Tree):
            return self.load(self.compileFunction(value))
        try:
            return value.load(self)
        except TypeError:
            raise ValueError(
                f"Cannot load resource of type {type(value)}. It cannot be converted to a Number.")

    def toResource(self, value) -> Resource:
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

    def close(self) -> FileStructure:
        return self.fileStructure

    def currentNamespace(self) -> Namespace:
        return self.stack[-1]

    def popStack(self):
        self.stack.pop()

    def pushStack(self, namespaceType: NamespaceType):
        namespace = Namespace(self.currentNamespace(), namespaceType)
        self.stack.append(namespace)
        return namespace

    def getDebugLines(self, a, b):
        return self.code[a - 1].strip()
