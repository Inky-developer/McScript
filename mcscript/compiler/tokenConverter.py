"""
Converts Tokens to their corresponding resources.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Type, Union

from lark import Token

from mcscript.exceptions.compileExceptions import McScriptTypeError
from mcscript.lang.resource.FixedNumberResource import FixedNumberResource
from mcscript.lang.resource.NumberResource import NumberResource
from mcscript.lang.resource.SelectorResource import SelectorResource
from mcscript.lang.resource.StringResource import StringResource
from mcscript.lang.resource.StructResource import StructResource
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


def convertToken(token: Union[Token, str], compileState: CompileState) -> Union[Resource, ResourceType]:
    """
    Converts a by lark generated token to the appropriate resource class.

    ToDo: instead of returning Type[Resource] return ResourceType

    Args:
        token: the token
        compileState: the compile state

    Returns:
        either a resource or a resource class
    """
    if token.type in globals():
        return globals()[token.type](token, compileState)
    try:
        return DATATYPE(token, compileState)
    except KeyError:
        raise McScriptTypeError(f"Could not interpret token '{token}' as a resource", compileState)


def INTEGER(token: Token, _: CompileState) -> Resource:
    return NumberResource(int(token), None)


def DECIMAL(token: Token, _: CompileState) -> Resource:
    return FixedNumberResource.fromNumber(float(token))


def STRING(token: Token, compileState: CompileState) -> Resource:
    return StringResource(token[1:-1], context=compileState.currentContext())


def SELECTOR(token: Token, compileState: CompileState):
    return SelectorResource(token, True, compileState, compileState.currentContext())


def DATATYPE(token: Token, compileState: CompileState) -> Union[Type[Resource], StructResource]:
    try:
        return ResourceType(token.value)
    except ValueError:
        datatype = compileState.currentContext().find_resource(token)
        if datatype is not None and datatype.type() == ResourceType.STRUCT:
            # noinspection PyTypeChecker
            return datatype
        raise KeyError(f"Invalid datatype {token}")
