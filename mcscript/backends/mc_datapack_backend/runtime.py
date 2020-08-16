from __future__ import annotations

import json
from typing import Optional, TYPE_CHECKING

from mcscript.data.selector import Selector
from mcscript.data.selector.Selector import Selector
from mcscript.ir.components import FunctionNode, FunctionCallNode, CommandNode, MessageNode
from mcscript.utils.JsonTextFormat.objectFormatter import format_text, format_color

if TYPE_CHECKING:
    from mcscript.backends.mc_datapack_backend.McDatapackBackend import McDatapackBackend


def make_on_load_function(main: FunctionNode, backend: McDatapackBackend, init_constants: Optional[FunctionNode],
                          init_scoreboards: Optional[FunctionNode]) -> FunctionNode:
    """
    Creates the mcscript-datapack runtime on-load function.

    When the datapack is loaded, the following things should happen:
        * initialize all scoreboards
        * initialize all scoreboard constants
        * If in debug, set the main scoreboard as sidebar
        * Make a installation message
        * run main

    Args:
        main: The main function
        backend: the datapack backend
        init_constants: the function to initialize constants
        init_scoreboards: the function to initialize the scoreboards

    Returns:
        A new function node that executes those steps
    """
    commands = []

    if init_scoreboards:
        commands.extend(init_scoreboards.inner_nodes)

    if init_constants:
        commands.extend(init_constants.inner_nodes)

    if not backend.config.is_release and len(backend.ir_master.scoreboards) > 0:
        commands.append(CommandNode(f"scoreboard objectives setdisplay sidebar {backend.ir_master.scoreboards[0]}"))

    message = format_text("["), format_color(format_text(backend.config.project_name), "gold"), format_text("] loaded!")
    commands.append(MessageNode(MessageNode.MessageType.CHAT, json.dumps(message), selector=Selector("a", [])))

    commands.append(FunctionCallNode(main))

    return FunctionNode(backend.config.resource_specifier_main("load"), commands)
