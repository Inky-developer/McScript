"""
Converts Tokens to their corresponding resources.
"""
from __future__ import annotations

from typing import Type, TYPE_CHECKING, Union

from lark import Token

from src.mcscript.Exceptions import McScriptTypeError
from src.mcscript.lang.Resource.FixedNumberResource import FixedNumberResource
from src.mcscript.lang.Resource.NumberResource import NumberResource
from src.mcscript.lang.Resource.ResourceBase import Resource
from src.mcscript.lang.Resource.ResourceType import ResourceType
from src.mcscript.lang.Resource.SelectorResource import SelectorResource
from src.mcscript.lang.Resource.StringResource import StringResource
from src.mcscript.lang.Resource.StructResource import StructResource

if TYPE_CHECKING:
    from src.mcscript import CompileState


# ToDo: custom resource to hold resource types
def convertToken(token: Token, compileState: CompileState) -> Union[Resource, Type[Resource]]:
    if token.type in globals():
        return globals()[token.type](token, compileState)
    try:
        return DATATYPE(token, compileState)
    except KeyError:
        raise McScriptTypeError(f"Could not convert token {token}", token)


def NUMBER(token: Token, compileState: CompileState) -> Resource:
    return NumberResource(int(token), True)


def DECIMAL(token: Token, compileState: CompileState) -> Resource:
    return FixedNumberResource.fromNumber(float(token))


def STRING(token: Token, compileState: CompileState) -> Resource:
    return StringResource(token[1:-1], True, compileState.currentNamespace())


def SELECTOR(token: Token, compileState: CompileState):
    return SelectorResource(token, True)


def DATATYPE(token: Token, compileState: CompileState) -> Union[Type[Resource], StructResource]:
    try:
        return Resource.getResourceClass(ResourceType(token.value))
    except ValueError:
        datatype = compileState.currentNamespace()[token]
        if datatype.type() == ResourceType.STRUCT:
            # noinspection PyTypeChecker
            return datatype
        raise ValueError(f"Invalid datatype {token}")
