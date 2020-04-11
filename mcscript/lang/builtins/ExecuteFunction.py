from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.lang.builtins.builtins import BuiltinFunction
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class ExecuteFunction(BuiltinFunction):
    """
    parameter => [Static] string: String the string to execute
    runs a minecraft function directly and returns null
    """

    def name(self) -> str:
        return "execute"

    def returnType(self) -> ResourceType:
        return ResourceType.NULL

    def generate(self, compileState: CompileState, *parameters: Resource) -> str:
        string, = parameters

        return str(string)
