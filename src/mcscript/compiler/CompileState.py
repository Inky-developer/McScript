from typing import List, Callable

from lark import Tree

from src.mcscript.compiler.Namespace import Namespace
from src.mcscript.data.Config import Config
from src.mcscript.lang.Resource.AddressResource import AddressResource
from src.mcscript.lang.Resource.ResourceBase import Resource
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

        self.stack: List[Namespace] = [Namespace()]
        self.namespaceTotal = 1

        self.fileStructure = self.datapack.getMainDirectory().getPath("functions").fileStructure
        self.lineCount = 0

        self._nextNamespaceDefaults: List[str] = []

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

    def pushBlock(self) -> AddressResource:
        """ creates a new file and namespace and returns the block id."""
        blockName = self.codeBlockStack.next()
        self.fileStructure.pushFile(blockName)
        self.pushStack()
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

    def pushStack(self):
        namespace = Namespace(self.currentNamespace())
        # for value, resource in self.nextNamespaceDefaults:
        #     # pre-calculate addresses for scoreboard numbers
        #     # ToDo: remove this bullshit and add function that are compiled each time they are called
        #     if resource.type() == ResourceType.NUMBER:
        #         namespace[value] = NumberVariableResource(namespace.variableFmt.format(value), False)
        #     elif resource.type() == ResourceType.FIXED_POINT:
        #         namespace[value] = FixedNumberVariableResource(namespace.variableFmt.format(value), False)
        self.nextNamespaceDefaults = []
        self.stack.append(namespace)

    def getDebugLines(self, a, b):
        return self.code[a - 1].strip()
