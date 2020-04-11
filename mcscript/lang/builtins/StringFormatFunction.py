from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.lang.builtins.builtins import BuiltinFunction, FunctionResult
from mcscript.lang.resource.StringResource import StringResource
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class StringFormatFunction(BuiltinFunction):
    """
    parameter => [Static] string: String the string to format
    parameter => [Static] *args: Resource the values to substitute into this string
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
        string: StringResource

        string, *parameters = parameters
        string = string.format(*parameters)

        return FunctionResult(None, string)
