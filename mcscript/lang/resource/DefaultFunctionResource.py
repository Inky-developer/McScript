from __future__ import annotations

import re
from typing import Dict, List, Optional, TYPE_CHECKING

from lark import Tree

from mcscript.compiler.ContextType import ContextType
from mcscript.data.commands import Command
from mcscript.exceptions.compileExceptions import McScriptArgumentsError, McScriptTypeError
from mcscript.lang.resource.AddressResource import AddressResource
from mcscript.lang.resource.NullResource import NullResource
from mcscript.lang.resource.TypeResource import TypeResource
from mcscript.lang.resource.base.FunctionResource import FunctionResource, Parameter
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


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
        compileState.pushBlock(ContextType.FUNCTION, blockName)

        self.initNamespace(compileState)

        for child in self.block.children:
            compileState.compileFunction(child)

        self.returnValue = compileState.currentContext().return_resource
        if self.returnValue.type() != self.returnType.value.type():
            raise McScriptTypeError(f"{repr(self)} should return {self.returnType.value.type().name} "
                                    f"but returned {self.returnValue.type().name}", compileState)

        # leave the signature as a comment
        signature = f"# fun {self.name()}({{}}) -> {{}}"
        params = ", ".join(
            f"{compileState.currentContext().find_resource(pIdentifier)}: {pType}" for pIdentifier, pType in
            self.parameters
        )
        compileState.writeline(signature.format(params, repr(self.returnValue)))

        compileState.popStack()
        compileState.fileStructure.popFile()

    def operation_call(self, compileState: CompileState, *parameters: Resource,
                       **keywordParameters: Resource) -> Resource:
        assert not keywordParameters
        parameters = self.signature.matchParameters(compileState, parameters)

        for parameter, pData in zip(parameters, self.parameters):
            pName, pType = pData

            # copy the parameters value to the namespace
            try:
                target = self.parameterStack[pName]
                if not isinstance(target, ValueResource):
                    raise TypeError(f"Unexpected type: {type(target)}")
                parameter.copy(target, compileState)
            except TypeError:
                raise McScriptArgumentsError(f"Failed to copy parameter {pName}.", compileState)

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
        returns whether this function can use its own name as a filename for the function file
        """
        return (
                compileState.currentContext().index == 0 and
                re.fullmatch(r"[a-z_]+", self.name())
        )

    def initNamespace(self, compileState: CompileState):
        for identifier, resource in self.parameters:
            resource = resource.value.createEmptyResource(identifier, compileState)
            self.parameterStack[identifier] = resource.value
            compileState.currentContext().add_var(identifier, resource)
