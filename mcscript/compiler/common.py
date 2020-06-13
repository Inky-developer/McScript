"""
Code that is often used on an ast.
"""
from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from lark import Tree

from mcscript import Logger
from mcscript.compiler.Context import Context
from mcscript.compiler.ContextType import ContextType
from mcscript.data import defaultEnums
from mcscript.data.commands import Command, ConditionalExecute, ExecuteCommand
from mcscript.exceptions.compileExceptions import McScriptNameError, McScriptSyntaxError, McScriptTypeError
from mcscript.exceptions.utils import requireType
from mcscript.lang.resource.SelectorResource import SelectorResource
from mcscript.lang.resource.base.ResourceBase import ObjectResource, Resource
from mcscript.lang.resource.base.VariableResource import VariableResource

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


def get_property(compileState: CompileState, accessor: Tree) -> List[Resource]:
    """
    Gets a (possibly nested) property of an object from the given accessor tree

    Args:
        compileState: the compile state
        accessor: the accessor tree

    Returns:
        A list of those objects that were accessed, where the last element is the wanted value
    """
    if accessor.data != "accessor":
        raise TypeError(f"Expected tree of type accessor, got type {accessor.data}")

    ret, *values = accessor.children

    if ret not in compileState.currentContext():
        # enums are loaded here lazily
        if result := defaultEnums.get(ret):
            compileState.stack.stack[0].add_var(ret, result)
        else:
            raise McScriptNameError(f"Unknown variable '{ret}'", compileState)

    accessed = [compileState.currentContext().find_resource(ret)]
    for value in values:
        try:
            accessed.append(accessed[-1].getAttribute(compileState, value))
        except TypeError:
            raise McScriptTypeError(f"Cannot access property '{value}' of {accessed[-1].type().value}",
                                    compileState)
    return accessed


def set_variable(compileState: CompileState, name: str, value: Resource):
    """
    Sets a variable which lives inside of a namespace and not inside of an object.

    Args:
        compileState: the compile state
        name: the identifier of the variable
        value: the value that should be assigned to the variable

    Returns:
        None
    """

    var = compileState.currentContext().find_resource(name)
    if not isinstance(var, VariableResource):
        raise McScriptTypeError(f"Expected '{name}' to be a variable, but got {var}", compileState)
    compileState.currentContext().set_var(name, value.storeToNbt(var.value, compileState))


def set_property(compileState: CompileState, accessor: Tree, value: Resource):
    obj, *rest = accessor.children

    # if there is no rest obj is a simple variable, no object
    if not rest:
        return set_variable(compileState, obj, value)

    compileState.currentTree = obj  # manual setting because this method is called manually
    if obj not in compileState.currentContext():
        raise McScriptNameError(f"Unknown variable '{obj}'", compileState)
    obj = compileState.currentContext().find_resource(obj)

    for i in rest[:-1]:
        compileState.currentTree = i
        if not isinstance(obj, ObjectResource):
            raise McScriptTypeError(f"resource {obj} must be an object!", compileState)

        try:
            obj = obj.getAttribute(compileState, i)
        except AttributeError:
            raise McScriptNameError(f"property {i} of {obj} does not exist!", compileState)

    attribute = rest[-1]

    if not isinstance(obj, ObjectResource):
        raise McScriptTypeError(f"resource {obj} must be an object!", compileState)

    compileState.currentTree = rest[-1]
    obj.setAttribute(compileState, attribute, value)


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
