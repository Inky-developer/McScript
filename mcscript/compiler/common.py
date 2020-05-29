"""
Code that is often used on an ast.
"""
from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from lark import Tree

from mcscript import Logger
from mcscript.compiler.Context import Context
from mcscript.compiler.ContextType import ContextType
from mcscript.data.commands import Command, ConditionalExecute, ExecuteCommand
from mcscript.exceptions.compileExceptions import McScriptSyntaxError
from mcscript.exceptions.utils import requireType
from mcscript.lang.resource.SelectorResource import SelectorResource

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


def search_non_static_namespace_until(compileState: CompileState, context: Context) -> Optional[Context]:
    """
    Iterates down the context stack until it hits `context` or a context is not static in which case
    the non-static context will be returned

    Args:
        compileState: The compile state
        context: The context to stop searching at

    Returns:
        A context if a non-static namespace was found
    """
    current_context = compileState.currentContext()
    while current_context is not context and current_context is not None:
        if not current_context.context_type.hasStaticContext:
            return current_context
        current_context = context.predecessor

    return None


def conditional_loop(compileState: CompileState,
                     block: Tree,
                     conditionTree: Tree,
                     check_start: bool,
                     context: Optional[Tree] = None):
    blockName = compileState.pushBlock(ContextType.LOOP)
    for child in block.children:
        compileState.compileFunction(child)

    condition = compileState.toCondition(conditionTree)
    if condition.isStatic:
        if condition.condition:
            Logger.info(f"[Compiler] Loop at line {conditionTree.line} column {conditionTree.column} runs forever!")
        else:
            Logger.info(
                f"[Compiler] Loop at line {conditionTree.line} column {conditionTree.column} only runs once!"
            )

    if context is not None:
        contextCmd = Command.EXECUTE(
            sub=readContextManipulator([context], compileState),
            command=Command.RUN_FUNCTION(function=blockName)
        )
    else:
        contextCmd = Command.RUN_FUNCTION(function=blockName)

    compileState.writeline(condition(contextCmd))
    compileState.popBlock()

    condition = compileState.toCondition(conditionTree) if check_start else ConditionalExecute(True)
    compileState.writeline(condition(contextCmd))


def readContextManipulator(modifiers: List[Tree], compileState: CompileState):
    def for_(selector):
        requireType(selector, SelectorResource, compileState)
        return ExecuteCommand.AS(target=selector)

    def at(selector):
        requireType(selector, SelectorResource, compileState)
        return ExecuteCommand.AT(target=selector)

    def absolute(x, y, z):
        return ExecuteCommand.POSITIONED(x=str(x), y=str(y), z=str(z))

    def relative(x, y, z):
        return ExecuteCommand.POSITIONED(x="~" + str(x), y="~" + str(y), z="~" + str(z))

    def local(x, y, z):
        return ExecuteCommand.POSITIONED(x="^" + str(x), y="^" + str(y), z="^" + str(z))

    def anchor(value):
        value = str(value)
        if value not in ("feet", "eyes"):
            raise McScriptSyntaxError(f"Expected 'feet' or 'eyes' but got '{value}'", compileState)
        return ExecuteCommand.ANCHORED(anchor=value)

    command_table = {
        "context_for"     : for_,
        "context_at"      : at,
        "context_absolute": absolute,
        "context_relative": relative,
        "context_local"   : local,
        "context_anchor"  : anchor
    }

    command = ""
    for modifier in modifiers:
        compileState.currentTree = modifier
        name = modifier.data

        if name not in command_table:
            raise McScriptSyntaxError(f"Unknown modifier: '{name}'", compileState)

        args = [compileState.toResource(i) for i in modifier.children]
        command += command_table[name](*args)

    return command
