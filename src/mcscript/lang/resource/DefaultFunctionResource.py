from __future__ import annotations

from typing import List, TYPE_CHECKING, Optional, Dict

from lark import Tree

from src.mcscript.Exceptions import McScriptArgumentsError, McScriptTypeError
from src.mcscript.compiler.NamespaceType import NamespaceType
from src.mcscript.data.Commands import Command
from src.mcscript.lang.resource.AddressResource import AddressResource
from src.mcscript.lang.resource.NullResource import NullResource
from src.mcscript.lang.resource.TypeResource import TypeResource
from src.mcscript.lang.resource.base.FunctionResource import FunctionResource, Parameter
from src.mcscript.lang.resource.base.ResourceBase import Resource, ValueResource

if TYPE_CHECKING:
    from src.mcscript import CompileState


class DefaultFunctionResource(FunctionResource):
    """
    A "default" function creates in init a .mcfunction file that can be called.
    init:
        create a namespace that is prepopulated with empty non-static resources that match the parameters.
        push this namespace and a new block
    """

    def __init__(self, name: str, parameters: List[Parameter], returnType: TypeResource, block: Tree):
        super().__init__(name, parameters, returnType, block)
        self.blockName: Optional[str] = None
        self.parameterStack: Dict[str, AddressResource] = {}
        self.stackName = 0
        # the actual resource pointing to the result of this function
        self.returnValue: ValueResource = NullResource()

    def compile(self, compileState: CompileState):
        blockName = self.blockName = self.name() if self.canUseOwnName(compileState) else \
            compileState.codeBlockStack.next()
        compileState.pushBlock(blockName, NamespaceType.FUNCTION)

        self.initNamespace(compileState)

        for child in self.block.children:
            compileState.compileFunction(child)

        self.returnValue = compileState.currentNamespace().returnedResource
        if self.returnValue.type() != self.returnType.value.type():
            raise McScriptTypeError(f"{repr(self)} should return {self.returnType.value.type().name} "
                                    f"but returned {self.returnValue.type().name}")

        # leave the signature as a comment
        signature = f"# fun {self.name()}({{}}) -> {{}}"
        params = ", ".join(
            f"{compileState.currentNamespace()[pIdentifier]}: {pType}" for pIdentifier, pType in self.parameters
        )
        compileState.writeline(signature.format(params, repr(self.returnValue)))

        compileState.popStack()
        compileState.fileStructure.popFile()

    def operation_call(self, compileState: CompileState, *parameters: Resource,
                       **keywordParameters: Resource) -> Resource:
        assert not keywordParameters

        if len(parameters) != len(self.parameters):
            raise McScriptArgumentsError(
                f"Invalid arguments: required {len(self.parameters)} but got {len(parameters)}")

        for parameter, pData in zip(parameters, self.parameters):
            pName, pType = pData

            if parameter.type() != pType.value.type():
                raise McScriptArgumentsError(
                    f"{repr(self)} got argument {parameter} with invalid type {parameter.type().name}, "
                    f"expected {pType.value.type().name}"
                )

            # copy the parameters value to the namespace
            try:
                target = self.parameterStack[pName]
                if not isinstance(target, ValueResource):
                    raise Exception(f"Unexpected type: {type(target)}")
                parameter.copy(target, compileState)
            except TypeError:
                raise McScriptArgumentsError(f"Failed to copy parameter {pName}.")

        # run the function
        compileState.writeline(Command.RUN_FUNCTION(function=self.blockName))

        if self.returnValue.isStatic:
            return self.returnValue

        # make sure to use a correct stack. Otherwise values could be overridden accidentally
        # if a function has return stack .exp0 it should be transferred to whatever is in the current context
        # the stack value
        stack = compileState.expressionStack.next()
        return self.returnValue.copy(stack, compileState) if self.returnValue.value != stack else self.returnValue

    def canUseOwnName(self, compileState: CompileState) -> bool:
        """
        :return: whether this function can use its own name as a filename for the function file
        """
        return (
                compileState.currentNamespace().index == 0 and
                self.name().isalpha() and
                self.name().islower()
        )

    def initNamespace(self, compileState: CompileState):
        for identifier, resource in self.parameters:
            resource = resource.value.createEmptyResource(identifier, compileState)
            self.parameterStack[identifier] = resource.value
            compileState.currentNamespace()[identifier] = resource
