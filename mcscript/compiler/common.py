"""
Code that is often used on an ast.
"""
from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from lark import Tree

from mcscript import Logger
from mcscript.analyzer import VariableContext
from mcscript.compiler.ContextType import ContextType
from mcscript.data import defaultEnums
from mcscript.exceptions.compileExceptions import (McScriptNameError, McScriptSyntaxError, McScriptTypeError,
                                                   McScriptError)
from mcscript.exceptions.utils import requireType
from mcscript.ir import IRNode
from mcscript.ir.command_components import Position, ExecuteAnchor, ScoreRange
from mcscript.ir.components import ExecuteNode, FunctionCallNode, ConditionalNode
from mcscript.lang.atomic_types import Selector as SelectorType
from mcscript.lang.resource.SelectorResource import SelectorResource
from mcscript.lang.resource.StringResource import StringResource
from mcscript.lang.resource.StructObjectResource import StructObjectResource
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

    # A resource is kept static as long as possible.
    # However, if it gets loaded in a non-static context,
    # in which it is also written to, it has to be stored on a scoreboard.
    if isinstance(parent_resource, ValueResource):
        if parent_resource.static_value is not None:
            if parent_var.context is None:
                raise ValueError("Could not find the context for resource")
            if has_resource_writes_in_this_context(compileState, parent_resource, parent_var.context):
                if not check_context_static(compileState, parent_resource, parent_var.context):
                    with compileState.ir.with_previous():
                        parent_resource = parent_resource.store(compileState)
                    accessed = [parent_resource]
                    # marks the variable in all contexts as non-static
                    compileState.currentContext().set_var(ret, parent_resource)
    # similar applies for objects
    elif isinstance(parent_resource, StructObjectResource) and parent_resource.is_any_static:
        if parent_var.context is None:
            raise ValueError("Could not find the context for the object resource")
        if has_resource_writes_in_this_context(compileState, parent_resource, parent_var.context):
            if not check_context_static(compileState, parent_resource, parent_var.context):
                with compileState.ir.with_previous():
                    parent_resource = parent_resource.store(compileState)
                accessed = [parent_resource]
                compileState.currentContext().set_var(ret, parent_resource)

    for value in values:
        try:
            accessed.append(accessed[-1].getAttribute(compileState, value))
        except TypeError:
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


def check_context_static(compileState: CompileState, resource: Resource, variable_context=None) -> bool:
    """
    Core concept: Variables keep their static value (if known) as long as possible and 
    will only be stored in a data storage or a scoreboard if it is not possible to calculate
    their value somehow at compile-time. If the initial value of a variable is statically known,
    it will only stop beeing static if accessed in a non-static context.

    A context is considered non-static for a variable if the variable is not defined in the same
    context and, walking up the context-stack until the context in which the variable got
    defined is hit, a non-static context exists
    """
    if variable_context is None:
        name = compileState.currentContext().find_resource_name(resource)

        if name is None:
            raise ValueError(f"The resource '{resource}' is not a variable")

        variable_context = compileState.currentContext().find_var(name).context

        if variable_context is None:
            raise ValueError(
                f"The variable '{name}' ('{resource}') does not have an associated context")

    return compileState.currentContext().search_non_static_until(
        compileState.stack.search_by_pos(
            *variable_context.declaration.master_context)
    ) is None  # and not variable context? (TODO)


def has_resource_writes_in_this_context(compileState: CompileState, resource: Resource,
                                        variable_context: VariableContext) -> bool:
    """
    Returns whether this resource has any writes in the current context.
    """
    writes = variable_context.writes
    for write in writes:
        context = compileState.stack.search_by_pos(*write.master_context)
        if context == compileState.currentContext():
            return True

    return False


def conditional_loop(compileState: CompileState,
                     block: Tree,
                     conditionTree: Tree,
                     check_start: bool,
                     context: Optional[Tree] = None):
    # ToDO: change to while node
    with compileState.node_block(ContextType.LOOP, block.line, block.column) as block_name:
        for child in block.children:
            compileState.compileFunction(child)

        condition_boolean = compileState.toResource(
            conditionTree).convertToBoolean(compileState)
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

        function_call_node = FunctionCallNode(
            compileState.resource_specifier_main(block_name))
        if context is not None:
            context_node = ExecuteNode(
                readContextManipulator([context], compileState),
                [function_call_node]
            )
        else:
            context_node = function_call_node

        compileState.ir.append(ConditionalNode(
            [ConditionalNode.IfScoreMatches(
                condition_boolean.value, ScoreRange(0), True)],
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
    def for_(selector: SelectorResource) -> IRNode:
        requireType(selector, SelectorType, compileState)
        return ExecuteNode.As(selector.static_value)

    def at(selector: SelectorResource) -> IRNode:
        requireType(selector, SelectorType, compileState)
        return ExecuteNode.At(selector.static_value)

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
            raise McScriptSyntaxError(
                f"Unknown modifier: '{name}'", compileState)

        args = [compileState.toResource(i) for i in modifier.children]
        command_nodes.append(command_table[name](*args))

    return command_nodes
