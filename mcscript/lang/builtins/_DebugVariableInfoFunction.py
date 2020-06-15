from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript import Logger
from mcscript.exceptions.utils.sourceAnnotation import SourceAnnotation, SourceAnnotationList
from mcscript.lang.builtins.builtins import BuiltinFunction, FunctionResult
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.resource.base.ResourceType import ResourceType
from mcscript.lang.resource.StringResource import StringResource

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
        variable = compileState.currentContext().find_var(identifier)
        variableData, resource = variable.context, variable.resource

        lines = []

        modifiers = "static " if variableData.static_declaration else ""
        modifiers += "mutable " if variableData.writes else "constant "
        lines.append(f"{modifiers}variable {identifier} of type {resource.type().value}")
        lines.append(f"Current value: {repr(resource)}")

        source_annotations = SourceAnnotationList()
        source_annotations += SourceAnnotation.from_token(compileState.code, variableData.declaration.access,
                                                          "Declared here")
        for accessType, var in variableData.history():
            # context = compileState.stack.search_by_pos(*var.master_context)
            message = "Read access here" if accessType == "read" else "Write access here"

            # what should that mean?
            # if not context.isContextStatic():
            #     message += f"\nNon-static context"

            source_annotations += SourceAnnotation.from_token(compileState.code, var.access, message)
        lines.append(str(source_annotations.sorted()))

        text = "\n".join(lines)
        Logger.info(f"Debug info for variable:\n{text}")

        return FunctionResult(None, StringResource(text, True))
