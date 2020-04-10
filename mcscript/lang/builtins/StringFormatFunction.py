from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.Exceptions.compileExceptions import McScriptArgumentsError, McScriptTypeError
from mcscript.lang.builtins.builtins import BuiltinFunction, FunctionResult
from mcscript.lang.resource.StringResource import StringResource
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class StringFormatFunction(BuiltinFunction):
    """
    parameter => string: String the string to format
    parameter => [List] args the values to substitute into this string
    Used so format strings can be store normally and replaced later using this function.
    example:
        const template = "setblock $ $ $ $"
        execute(stringFormat(template, 0, 0, 0, blocks.stone))
    """

    def name(self) -> str:
        return "stringFormat"

    def returnType(self) -> ResourceType:
        return ResourceType.STRING

    def generate(self, compileState: CompileState, *parameters: Resource) -> FunctionResult:
        if len(parameters) < 1:
            raise McScriptArgumentsError("The function stringFormat expects at least one argument.")
        string, *parameters = parameters
        if not isinstance(string, StringResource):
            raise McScriptTypeError("stringFormat function expected first argument to be of type String.")
        if not string.isStatic:
            raise McScriptTypeError("the string argument for the stringFormat function must be static.")

        if not all(isinstance(i, ValueResource) for i in parameters):
            raise McScriptArgumentsError("All arguments for the stringFormat function have to be values.")

        string = string.format(*parameters)

        return FunctionResult(None, string)
