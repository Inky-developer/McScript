"""
Converts Tokens to their corresponding resources.
"""
from __future__ import annotations

from collections import ChainMap
from typing import TYPE_CHECKING, Union

from lark import Token

from mcscript.exceptions.McScriptException import McScriptError
from mcscript.exceptions.exceptions import McScriptValueError
from mcscript.lang.Type import Type
from mcscript.lang.atomic_types import ATOMIC_TYPES
from mcscript.lang.resource.FixedNumberResource import FixedNumberResource
from mcscript.lang.resource.IntegerResource import IntegerResource
from mcscript.lang.resource.SelectorResource import SelectorResource
from mcscript.lang.resource.StringResource import StringResource
from mcscript.lang.resource.base.ResourceBase import Resource

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


def convert_token_to_resource(token: Union[Token, str], compile_state: CompileState) -> Resource:
    """
    Converts a by lark generated token to the appropriate resource class.

    Args:
        token: the token
        compile_state: the compile state

    Returns:
        a resource
    """
    functions = {
        "INTEGER": lambda: IntegerResource(int(token), None),
        "DECIMAL": lambda: FixedNumberResource.fromNumber(float(token)),
        "STRING": lambda: StringResource(token[1:-1], context=compile_state.currentContext()),
        "SELECTOR": lambda: SelectorResource(token, compile_state)
    }
    if token.type in functions:
        return functions[token.type]()
    raise McScriptError(f"Could not interpret token '{token}' as a resource", compile_state)


def convert_token_to_type(token: Token, compile_state: CompileState) -> Type:
    if token.type != "IDENTIFIER":
        raise ValueError(f"Invalid token: got {token.type}, expected IDENTIFIER")

    all_types = ChainMap(ATOMIC_TYPES, compile_state.custom_types)

    try:
        return all_types[token]
    except KeyError:
        print(all_types)
        raise McScriptValueError(token, "a valid type", compile_state)
