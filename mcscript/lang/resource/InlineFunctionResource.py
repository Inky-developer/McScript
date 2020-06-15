from __future__ import annotations

from typing import List, TYPE_CHECKING

from lark import Tree

from mcscript.compiler.ContextType import ContextType
from mcscript.exceptions.compileExceptions import McScriptTypeError
from mcscript.lang.resource.base.FunctionResource import FunctionResource
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.lang.resource.TypeResource import TypeResource
from mcscript.lang.utility import compareTypes

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class InlineFunctionResource(FunctionResource):
    isDefault = False

    def __init__(self, name: str, parameters: List, return_type: TypeResource,
                 block: Tree):
        super().__init__(name, parameters, return_type, block)

    def operation_call(self, compileState: CompileState, *parameters: Resource,
                       **keywordParameters: Resource) -> Resource:
        parameters = self.signature.matchParameters(compileState, parameters)

        context = compileState.pushContext(ContextType.INLINE_FUNCTION, self.block.line, self.block.column)

        for pTemplate, parameter in zip(self.parameters, parameters):
            pName, pType = pTemplate
            parameter = self._loadParameter(parameter, pName, pType, compileState)
            context.add_var(pName, parameter)

        self.executeBody(compileState)

        if not compareTypes(context.get_return_resource_or_null(), self.returnType.value):
            raise McScriptTypeError(f"Function {self.name()} should return {self.returnType.value.type().name}, "
                                    f"but returned {context.return_resource.type().name}", compileState)

        compileState.popContext()
        return context.get_return_resource_or_null()

    def executeBody(self, compileState: CompileState):
        for child in self.block.children:
            compileState.compileFunction(child)

    @staticmethod
    def inline() -> bool:
        return True

    def _loadParameter(self, parameter: Resource, pName: str, pType: TypeResource,
                       compileState: CompileState) -> Resource:
        """
        How resources are dealt with in inline functions.
        As there should be as few overhead as possible, resources that must be inlined and static values
        get directly passed on to this function. This has the side effect that, if these resources get modified, they
        will change their value outside of this function scope. This is wanted for struct objects and static values
        are currently not allowed to be modified so there is no problem with passing them.
        """
        if pType.value.requiresInlineFunc or (isinstance(parameter, ValueResource) and parameter.isStatic):
            return parameter

        return parameter.load(compileState).storeToNbt(
            compileState.get_nbt_address(pName),
            compileState
        )
