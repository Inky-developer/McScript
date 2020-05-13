from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript import Logger
from mcscript.exceptions.utils.sourceAnnotation import SourceAnnotation, SourceAnnotationList
from mcscript.lang.builtins.builtins import BuiltinFunction, FunctionResult
from mcscript.lang.resource.StringResource import StringResource
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class _DebugVariableInfoFunction(BuiltinFunction):
    """
    parameter => resource: String the resource

    """

    def name(self) -> str:
        return "_DebugVariable"

    def returnType(self) -> ResourceType:
        return ResourceType.STRING

    def generate(self, compileState: CompileState, *parameters: Resource) -> FunctionResult:
        variable, = parameters
        identifier = variable.toString()
        variableData = compileState.currentNamespace().getVariableInfo(compileState, identifier)
        resource = compileState.currentNamespace()[identifier]

        lines = []

        modifiers = "static " if variableData.static_declaration else ""
        modifiers += "mutable " if variableData.writes else "constant "
        lines.append(f"{modifiers}variable {identifier} of type {resource.type().value}")
        lines.append(f"Current value: {repr(resource)}")

        source_annotations = SourceAnnotationList()
        source_annotations += SourceAnnotation.from_token(compileState.code, variableData.declaration.access,
                                                          "Declared here")
        for accessType, var in variableData.history():
            namespace = compileState.stack.getByIndex(var.contextId)
            message = "Read access here" if accessType == "read" else "Write access here"
            if not namespace.isContextStatic():
                message += f"\nNon-static context"
            source_annotations += SourceAnnotation.from_token(compileState.code, var.access, message)
        lines.append(str(source_annotations.sorted()))

        text = "\n".join(lines)
        Logger.info(f"Debug info for variable:\n{text}")

        return FunctionResult(None, StringResource(text, True))
