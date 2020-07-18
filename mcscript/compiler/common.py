"""
Code that is often used on an ast.
"""
from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from lark import Tree

from mcscript import Logger
from mcscript.compiler.ContextType import ContextType
from mcscript.data import defaultEnums
from mcscript.exceptions.compileExceptions import (McScriptNameError, McScriptSyntaxError, McScriptTypeError,
                                                   McScriptError)
from mcscript.exceptions.utils import requireType
from mcscript.ir.command_components import Position, ExecuteAnchor, ScoreRange
from mcscript.ir.components import ExecuteNode, FunctionCallNode, ConditionalNode
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

    # A variable does not have to be a variable resource, because it can be stored as static.
    # if not isinstance(var, VariableResource):
    #     raise McScriptTypeError(f"Expected '{name}' to be a variable, but got {var}", compileState)

    # if the previous value was not static, the new one should not be either
    if isinstance(var, VariableResource):
        value = value.storeToNbt(var.value, compileState)

    if var is None:
        # if the variable is new check if it is ever written to.
        # if yes, cal `store()` on the variable
        variable_context = compileState.currentContext().variable_context.get(name)
        is_const = variable_context is not None and len(variable_context.writes) == 0

        if not is_const:
            value = value.storeToNbt(compileState.get_nbt_address(name), compileState)

        compileState.currentContext().add_var(name, value)
    else:
        compileState.currentContext().set_var(name, value)


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


def check_context_static(compileState: CompileState, resource: Resource) -> bool:
    name = compileState.currentContext().find_resource_name(resource)

    if name is None:
        raise ValueError(f"The resource '{resource}' is not a variable")

    variable_context = compileState.currentContext().find_var(name).context

    if variable_context is None:
        raise ValueError(f"The variable '{name}' ('{resource}') does not have an associated context")

    return compileState.currentContext().search_non_static_until(
        compileState.stack.search_by_pos(*variable_context.declaration.master_context)
    ) is None


def conditional_loop(compileState: CompileState,
                     block: Tree,
                     conditionTree: Tree,
                     check_start: bool,
                     context: Optional[Tree] = None):
    # ToDO: change to while node
    with compileState.node_block(ContextType.LOOP, block.line, block.column) as block_name:
        for child in block.children:
            compileState.compileFunction(child)

        condition_boolean = compileState.toResource(conditionTree).convertToBoolean(compileState)
        if condition_boolean.isStatic:
            if condition_boolean.value is True:
                Logger.error(
                    f"[Compiler] Loop at line {conditionTree.line} column {conditionTree.column} runs forever!")
                # ToDO create exception for that
                raise McScriptError("Loop runs forever", compileState)
            else:
                Logger.warning(
                    f"[Compiler] Loop at line {conditionTree.line}, column {conditionTree.column} "
                    f"only runs once / not at all!"
                )

        function_call_node = FunctionCallNode(compileState.resource_specifier_main(block_name))
        if context is not None:
            context_node = ExecuteNode(
                readContextManipulator([context], compileState),
                [function_call_node]
            )
        else:
            context_node = function_call_node

        compileState.ir.append(ConditionalNode(
            [ConditionalNode.IfScoreMatches(condition_boolean.value, ScoreRange(0), True)],
            [context_node]
        ))

    if check_start:
        compileState.ir.append(ConditionalNode(
            [ConditionalNode.IfScoreMatches(compileState.toResource(conditionTree).convertToBoolean(compileState).value,
                                            ScoreRange(0), True)],
            [context_node]
        ))
    else:
        compileState.ir.append(context_node)


def readContextManipulator(modifiers: List[Tree], compileState: CompileState) -> List[ExecuteNode.ExecuteArgument]:
    def for_(selector):
        requireType(selector, SelectorResource, compileState)
        return ExecuteNode.As(selector.value)

    def at(selector):
        requireType(selector, SelectorResource, compileState)
        return ExecuteNode.At(selector.value)

    def absolute(x, y, z):
        return ExecuteNode.Positioned(Position.absolute(float(x), float(y), float(z)))

    def relative(x, y, z):
        return ExecuteNode.Positioned(Position.relative(float(x), float(y), float(z)))

    def local(x, y, z):
        return ExecuteNode.Positioned(Position.local(float(x), float(y), float(z)))

    def anchor(value):
        try:
            value = ExecuteAnchor(str(value))
        except ValueError:

            raise McScriptSyntaxError(f"'{value}' is not a valid execute anchor."
                                      f"Expected one of {', '.join(i.value for i in ExecuteAnchor)}", compileState)
        return ExecuteNode.Anchored(value)

    command_table = {
        "context_for": for_,
        "context_at": at,
        "context_absolute": absolute,
        "context_relative": relative,
        "context_local": local,
        "context_anchor": anchor
    }

    command_nodes = []
    for modifier in modifiers:
        compileState.currentTree = modifier
        name = modifier.data

        if name not in command_table:
            raise McScriptSyntaxError(f"Unknown modifier: '{name}'", compileState)

        args = [compileState.toResource(i) for i in modifier.children]
        command_nodes.append(command_table[name](*args))

    return command_nodes
