from __future__ import annotations

from typing import List, TYPE_CHECKING

from lark import Tree

from src.mcscript.Exceptions import McScriptArgumentsError, McScriptTypeError
from src.mcscript.compiler.NamespaceType import NamespaceType
from src.mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from src.mcscript.lang.resource.TypeResource import TypeResource
from src.mcscript.lang.resource.base.FunctionResource import FunctionResource, Parameter
from src.mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from src.mcscript.lang.utility import compareTypes

if TYPE_CHECKING:
    from src.mcscript import CompileState


class InlineFunctionResource(FunctionResource):
    isDefault = False

    def __init__(self, name: str, parameters: List[Parameter], return_type: TypeResource, block: Tree):
        super().__init__(name, parameters, return_type, block)

    def operation_call(self, compileState: CompileState, *parameters: Resource,
                       **keywordParameters: Resource) -> Resource:
        if len(self.parameters) != len(parameters):
            raise McScriptArgumentsError(
                f"Invalid function call: expected {len(self.parameters)} arguments, but got {len(parameters)}")

        namespace = compileState.pushStack(NamespaceType.FUNCTION)

        for pTemplate, parameter in zip(self.parameters, parameters):
            pName, pType = pTemplate
            parameter = self._loadParameter(parameter, pName, pType, compileState)
            if not compareTypes(parameter, pType.value):
                raise McScriptArgumentsError(f"Function call {self.name()}: expected type {pType.value.value} "
                                             f"for argument {pName}, but got type {parameter.type().value}")
            namespace[pName] = parameter

        # execute the body
        for child in self.block.children:
            compileState.compileFunction(child)

        if not compareTypes(namespace.returnedResource, self.returnType.value):
            raise McScriptTypeError(f"Function {self.name()} should return {self.returnType.type().name}, "
                                    f"but returned {namespace.returnedResource.type().name}")

        compileState.popStack()
        return namespace.returnedResource

    def _loadParameter(self, parameter: Resource, pName: str, pType: TypeResource,
                       compileState: CompileState) -> Resource:
        """
        How resources are dealt with in inline functions.
        As there should be as few overhead as possible, resources that must be inlined and static values
        get directly passed on to this function. This has the side effect that, if these resources get modified, they
        will change their value outside of this function scope. This is wanted for struct objects and static value
        are currently not allowed to be modified so there is no problem with passing them.
        """
        if pType.value.requiresInlineFunc or (isinstance(parameter, ValueResource) and parameter.isStatic):
            return parameter
        return parameter.load(compileState).storeToNbt(
            NbtAddressResource(compileState.currentNamespace().variableFmt.format(pName)),
            compileState
        )
