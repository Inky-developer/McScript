from __future__ import annotations

from typing import TYPE_CHECKING, Union

from mcscript.exceptions.compileExceptions import McScriptArgumentsError
from mcscript.lang.builtins.builtins import BuiltinFunction, FunctionResult
from mcscript.lang.resource.StringResource import StringResource
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class ExecuteFunction(BuiltinFunction):
    """
    parameter => string: String the string to execute
    runs a minecraft function directly and returns null
    """

    def name(self) -> str:
        return "execute"

    def returnType(self) -> ResourceType:
        return ResourceType.NULL

    def generate(self, compileState: CompileState, *parameters: Resource) -> Union[str, FunctionResult]:
        string: StringResource
        string, = parameters

        if string.isStatic:
            return str(string)

        raise McScriptArgumentsError(f"Function execute cannot work with non-static strings yet. "
                                     f"Use execute with a const string", compileState)

        # # else set a command block at 0, 0
        # return FunctionResult(
        #     multiple_commands(
        #         Command.SET_BLOCK(
        #             x=0,
        #             y=0,
        #             z=0,
        #             block=Blocks.findBlockByName("command_block").minecraft_id,
        #             nbt="{auto:1b}"
        #         ),
        #         Command.MODIFY_BLOCK_FROM_VARIABLE(
        #             x=0,
        #             y=0,
        #             z=0,
        #             path="Command",
        #             address=string.value
        #         )
        #     ),
        #     NullResource()
        # )
