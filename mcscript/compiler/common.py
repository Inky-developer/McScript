"""
Code that is often used on an ast.
"""
from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from lark import Tree

from mcscript import Logger
from mcscript.analyzer.VariableContext import VariableContext
from mcscript.compiler.Namespace import Namespace
from mcscript.compiler.NamespaceType import NamespaceType
from mcscript.data.commands import Command, ConditionalExecute, ExecuteCommand
from mcscript.exceptions.compileExceptions import McScriptSyntaxError
from mcscript.exceptions.utils import requireType
from mcscript.lang.resource.SelectorResource import SelectorResource

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


def get_context_info(compileState: CompileState, tree: Tree) -> VariableContext:
    if tree.data == "accessor":
        name, = tree.children
    else:
        raise ValueError(f"Cannot get variable name from tree {tree}")

    return compileState.currentNamespace().getVariableInfo(compileState, name)


def search_non_static_namespace_until(compileState: CompileState, namespace: Namespace) -> Optional[Namespace]:
    """
    Iterates down the namespace stack until it hits `namespace` or a namespace is not static in which case
    the non-static namespace will be returned

    Args:
        compileState: The compile state
        namespace: The namespace to stop searching at

    Returns:
        A namespace if a non-static namespace was found
    """
    current_namespace = compileState.currentNamespace()
    while current_namespace is not namespace and current_namespace is not None:
        if not current_namespace.namespaceType.hasStaticContext:
            return current_namespace
        current_namespace = namespace.predecessor

    return None


def conditional_loop(compileState: CompileState,
                     block: Tree,
                     conditionTree: Tree,
                     check_start: bool,
                     context: Optional[Tree] = None):
    blockName = compileState.pushBlock(namespaceType=NamespaceType.LOOP)
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
