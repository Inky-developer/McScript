"""
Code that is often used on an ast.
"""
from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from lark import Tree

from mcscript.compiler.ContextType import ContextType
from mcscript.data import defaultEnums
from mcscript.exceptions.compileExceptions import (McScriptNameError, McScriptSyntaxError, McScriptTypeError)
from mcscript.exceptions.utils import requireType
from mcscript.ir import IRNode
from mcscript.ir.command_components import Position, ExecuteAnchor, ScoreRange
from mcscript.ir.components import ExecuteNode, FunctionCallNode, ConditionalNode, FunctionNode, IfNode
from mcscript.lang.atomic_types import Selector as SelectorType, Bool
from mcscript.lang.resource.BooleanResource import BooleanResource
from mcscript.lang.resource.SelectorResource import SelectorResource
from mcscript.lang.resource.StringResource import StringResource
from mcscript.lang.resource.base.ResourceBase import ObjectResource, Resource, ValueResource

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
        raise TypeError(
            f"Expected tree of type accessor, got type {accessor.data}")

    ret, *values = accessor.children

    if ret not in compileState.currentContext():
        # enums are loaded here lazily
        if result := defaultEnums.get(ret):
            compileState.stack.stack[0].add_var(ret, result)
        else:
            raise McScriptNameError(f"Unknown variable '{ret}'", compileState)

    parent_var = compileState.currentContext().find_var(ret)
    parent_resource = parent_var.resource
    accessed = [parent_resource]

    # # A resource is kept static as long as possible.
    # # However, if it gets loaded in a non-static context,
    # # in which it is also written to, it has to be stored on a scoreboard.
    # if isinstance(parent_resource, ValueResource):
    #     if parent_resource.static_value is not None:
    #         if parent_var.context is None:
    #             raise ValueError("Could not find the context for resource")
    #         if has_resource_writes_in_this_context(compileState, parent_resource, parent_var.context):
    #             if not check_context_static(compileState, parent_resource, parent_var.context):
    #                 with compileState.ir.with_previous():
    #                     parent_resource = parent_resource.store(compileState)
    #                 accessed = [parent_resource]
    #                 # marks the variable in all contexts as non-static
    #                 compileState.currentContext().set_var(ret, parent_resource)
    # # similar applies for objects
    # elif isinstance(parent_resource, StructObjectResource) and parent_resource.is_any_static:
    #     if parent_var.context is None:
    #         raise ValueError("Could not find the context for the object resource")
    #     if has_resource_writes_in_this_context(compileState, parent_resource, parent_var.context):
    #         if not check_context_static(compileState, parent_resource, parent_var.context):
    #             with compileState.ir.with_previous():
    #                 parent_resource = parent_resource.store(compileState)
    #             accessed = [parent_resource]
    #             compileState.currentContext().set_var(ret, parent_resource)

    for value in values:
        try:
            accessed.append(accessed[-1].getAttribute(compileState, value))
        except (TypeError, KeyError):
            raise McScriptTypeError(f"Cannot access property '{value}' of {accessed[-1].type()}",
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

    if var is None:
        # # if the variable is new check if it is ever written to.
        # # if yes, cal `store()` on the variable
        # variable_context = compileState.currentContext().variable_context.get(name)
        # is_const = variable_context is not None and len(variable_context.writes) == 0

        # if not is_const:
        #     value = value.store(compileState)

        compileState.currentContext().add_var(name, value)
    else:
        compileState.currentContext().set_var(name, value)


def set_property(compileState: CompileState, accessor: Tree, value: Resource):
    obj, *rest = accessor.children

    # if there is no rest obj is a simple variable, no object
    if not rest:
        return set_variable(compileState, obj, value)

    # manual setting because this method is called manually
    compileState.currentTree = obj
    if obj not in compileState.currentContext():
        raise McScriptNameError(f"Unknown variable '{obj}'", compileState)
    obj = compileState.currentContext().find_resource(obj)

    for i in rest[:-1]:
        compileState.currentTree = i
        if not isinstance(obj, ObjectResource):
            raise McScriptTypeError(
                f"resource {obj} must be an object!", compileState)

        try:
            obj = obj.getAttribute(compileState, i)
        except AttributeError:
            raise McScriptNameError(
                f"property {i} of {obj} does not exist!", compileState)

    attribute = rest[-1]

    if not isinstance(obj, ObjectResource):
        raise McScriptTypeError(
            f"resource {obj} must be an object!", compileState)

    compileState.currentTree = rest[-1]
    obj.setAttribute(compileState, attribute, value)


def conditional_loop(compile_state: CompileState,
                     block: Tree,
                     condition_tree: Tree,
                     check_start: bool,
                     context: Optional[Tree] = None):
    """
    Creates a recursive function call loop

    Args:
        compile_state: the compile state
        block: the block of the loop
        condition_tree: the condition
        check_start: If True checks the condition before entering the loop
        context: Additional parameters which change the execution context every loop

    Returns:
        None
    """

    def repeat_if(condition: Resource, function: FunctionNode):
        call_node = FunctionCallNode(function)
        if context is not None:
            call_node = ExecuteNode(readContextManipulator([context], compile_state), [call_node])

        if not isinstance(condition, BooleanResource):
            raise McScriptTypeError(f"Expected {Bool}, got {condition.type()}", compile_state)
        if condition.is_static:
            if not condition.static_value:
                return
            compile_state.ir.append(call_node)
            return

        compile_state.ir.append(IfNode(
            ConditionalNode([ConditionalNode.IfScoreMatches(condition.scoreboard_value, ScoreRange(0), True)]),
            call_node
        ))

    # 1. Create the new function
    with compile_state.node_block(ContextType.LOOP, block.line, block.column) as loop_function:

        # 2. Check the initial condition if needed
        # Yes, this seems ugly, but:
        #   * The initial condition has to be computed before the body is executed
        #   * The Conditional function node has to be directly below the initial condition so it can be optimized
        # Problem: variables might be not static even if their static value might still be usable (ToDo)
        with compile_state.ir.with_previous():
            if check_start:
                initial_condition = compile_state.toResource(condition_tree)
            else:
                initial_condition = BooleanResource(1, None)
            repeat_if(initial_condition, loop_function)

        # Now compute the loop body
        compile_state.compile_ast(block)

        # create recursion condition
        recurse_condition = compile_state.toResource(condition_tree)
        repeat_if(recurse_condition, loop_function)


def readContextManipulator(modifiers: List[Tree], compileState: CompileState) -> List[ExecuteNode.ExecuteArgument]:
    def for_(selector: SelectorResource) -> IRNode:
        requireType(selector, SelectorType, compileState)
        return ExecuteNode.As(selector.value)

    def at(selector: SelectorResource) -> IRNode:
        requireType(selector, SelectorType, compileState)
        return ExecuteNode.At(selector.value)

    def absolute(x: ValueResource, y: ValueResource, z: ValueResource) -> IRNode:
        return ExecuteNode.Positioned(
            Position.absolute(float(x.static_value), float(y.static_value), float(z.static_value)))

    def relative(x: ValueResource, y: ValueResource, z: ValueResource) -> IRNode:
        return ExecuteNode.Positioned(
            Position.relative(float(x.static_value), float(y.static_value), float(z.static_value)))

    def local(x: ValueResource, y: ValueResource, z: ValueResource) -> IRNode:
        return ExecuteNode.Positioned(
            Position.local(float(x.static_value), float(y.static_value), float(z.static_value)))

    def anchor(value: StringResource) -> IRNode:
        try:
            value = ExecuteAnchor(value.static_value)
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
            raise McScriptSyntaxError(
                f"Unknown modifier: '{name}'", compileState)

        args = [compileState.toResource(i) for i in modifier.children]
        command_nodes.append(command_table[name](*args))

    return command_nodes
