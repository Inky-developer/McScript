from __future__ import annotations

from typing import TYPE_CHECKING

from src.mcscript.Exceptions import McScriptArgumentsError, McScriptTypeError
from src.mcscript.data.builtins.builtins import BuiltinFunction, FunctionResult
from src.mcscript.lang.Resource.ResourceBase import Resource, ValueResource
from src.mcscript.lang.Resource.ResourceType import ResourceType
from src.mcscript.lang.Resource.StringResource import StringResource

if TYPE_CHECKING:
    from src.mcscript import CompileState


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
        if len(parameters) <= 1:
            raise McScriptArgumentsError("The function stringFormat expects at least two arguments.")
        string, *parameters = parameters
        if not isinstance(string, StringResource):
            raise McScriptTypeError("stringFormat function expected first argument to be of type String.")
        if not string.isStatic:
            raise McScriptTypeError("the string argument for the stringFormat function must be static.")

        if not all(isinstance(i, ValueResource) for i in parameters):
            raise McScriptArgumentsError("All arguments for the stringFormat function have to be values.")

        string = string.format(*parameters)

        return FunctionResult(None, string)
