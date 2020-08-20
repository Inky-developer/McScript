"""
Code that is often used on an ast.
"""
from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from lark import Tree

from mcscript.compiler.ContextType import ContextType
from mcscript.data import defaultEnums
from mcscript.exceptions.McScriptException import McScriptError
from mcscript.exceptions.exceptions import (McScriptUndefinedVariableError, McScriptUndefinedAttributeError,
                                            McScriptUnexpectedTypeError, McScriptValueError)
from mcscript.exceptions.utils import requireType
from mcscript.ir import IRNode
from mcscript.ir.command_components import Position, ExecuteAnchor
from mcscript.ir.components import ExecuteNode, FunctionCallNode, ConditionalNode, FunctionNode, IfNode
from mcscript.lang.atomic_types import Selector as SelectorType
from mcscript.lang.resource.SelectorResource import SelectorResource
from mcscript.lang.resource.StringResource import StringResource
from mcscript.lang.resource.base.ResourceBase import ObjectResource, Resource, ValueResource
from mcscript.lang.utility import is_static

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
        if result := defaultEnums.get(ret, compileState.config):
            compileState.stack.stack[0].add_var(ret, result)
        else:
            raise McScriptUndefinedVariableError(ret, compileState)

    parent_var = compileState.currentContext().find_var(ret)
    parent_resource = parent_var.resource
    accessed = [parent_resource]

    for value in values:
        try:
            accessed.append(accessed[-1].getAttribute(compileState, value))
        except (TypeError, KeyError):
            raise McScriptUndefinedAttributeError(accessed[-1].type(), value, compileState)
    return accessed


def declare_variable(compile_state: CompileState, name: str, value: Resource):
    """
    declares a variable which lives inside of a namespace and not inside of an object.

    Args:
        compile_state: the compile state
        name: the identifier of the variable
        value: the value that should be assigned to the variable

    Returns:
        None
    """

    context_data = compile_state.currentContext().variable_context.get(name, None)

    # Form: a = b, where b is already a variable. If a has any writes, it must be a copy of b
    if isinstance(value, ValueResource) and (not value.is_static) and value.is_variable:
        if context_data is None or context_data.writes:
            value = value.copy(compile_state.expressionStack.next(), compile_state)

    compile_state.currentContext().add_var(name, value)


def update_variable(compile_state: CompileState, name: str, value: Resource):
    """
    Updates a variable that was already declared.

    Args:
        compile_state: The compile state
        name: the name of the variable
        value: the value of the variable

    Returns:
        None
    """
    old_var = compile_state.currentContext().find_var(name)

    if old_var is None:
        raise McScriptUndefinedVariableError(name, compile_state)

    if not value.type().is_same_type(old_var.resource.type()):
        raise McScriptUnexpectedTypeError(name, value.type(), old_var.resource.type(), compile_state)

    # if the last value is dynamic and the new one is not, store the new value
    if not is_static(old_var.resource) and isinstance(value, ValueResource) and value.is_static:
        # noinspection PyUnresolvedReferences
        value = value.store(compile_state, old_var.resource.scoreboard_value)

    # if both values are dynamic, make sure they are at the same scoreboard address
    if not is_static(old_var.resource) and not is_static(value):
        # noinspection PyUnresolvedReferences
        if value.scoreboard_value != old_var.resource.scoreboard_value:
            # noinspection PyUnresolvedReferences
            value = value.copy(old_var.resource.scoreboard_value, compile_state)

    compile_state.currentContext().set_var(name, value)


def set_property(compile_state: CompileState, accessor: Tree, value: Resource):
    """
    Tries to set an already existing variable to a specific value.
    Defers to `update_variable` if accessor accesses a variable instead of a property

    Args:
        compile_state: the compile state
        accessor: the accessor tree
        value: the new value

    """
    obj, *rest = accessor.children

    if not rest:
        return update_variable(compile_state, obj, value)

    # manual setting because this method is called manually
    compile_state.currentTree = obj
    if obj not in compile_state.currentContext():
        raise McScriptUndefinedVariableError(obj, compile_state)
    obj = compile_state.currentContext().find_resource(obj)

    for i in rest[:-1]:
        compile_state.currentTree = i
        if not isinstance(obj, ObjectResource):
            raise McScriptUnexpectedTypeError("object", obj, "Object", compile_state)

        try:
            obj = obj.getAttribute(compile_state, i)
        except AttributeError:
            raise McScriptUndefinedAttributeError(obj, i, compile_state)

    attribute = rest[-1]

    if not isinstance(obj, ObjectResource):
        raise McScriptUnexpectedTypeError("Object", obj, "Object", compile_state)

    compile_state.currentTree = rest[-1]
    obj.setAttribute(compile_state, attribute, value)


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

    def repeat_if(condition: ConditionalNode, function: FunctionNode):
        call_node = FunctionCallNode(function)
        if context is not None:
            call_node = ExecuteNode(readContextManipulator([context], compile_state), [call_node])

        static_value = condition.static_value()
        if static_value is not None:
            if not static_value:
                return
            compile_state.ir.append(call_node)
            return

        compile_state.ir.append(IfNode(condition, call_node))

    # 1. Create the new function
    with compile_state.node_block(ContextType.LOOP, block.line, block.column) as loop_function:

        # 2. Check the initial condition if needed
        # Yes, this seems ugly, but:
        #   * The initial condition has to be computed before the body is executed
        #   * The Conditional function node has to be directly below the initial condition so it can be optimized
        # Problem: variables might be not static even if their static value might still be usable (ToDo)
        with compile_state.ir.with_previous():
            if check_start:
                initial_condition = compile_state.to_condition(condition_tree)
            else:
                initial_condition = ConditionalNode([ConditionalNode.IfBool(True)])
            repeat_if(initial_condition, loop_function)

        # Now compute the loop body
        compile_state.compile_ast(block)

        # create recursion condition
        recurse_condition = compile_state.to_condition(condition_tree)
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

            raise McScriptError(f"'{value}' is not a valid execute anchor."
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
            raise McScriptValueError(name, tuple(command_table.keys()), compileState)

        args = [compileState.toResource(i) for i in modifier.children]
        command_nodes.append(command_table[name](*args))

    return command_nodes
