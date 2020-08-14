from __future__ import annotations

from typing import Callable, TYPE_CHECKING, List

from mcscript.lang.Type import Type
from mcscript.lang.atomic_types import Null, Any
from mcscript.lang.resource.MacroResource import MacroResource
from mcscript.lang.resource.base.functionSignature import FunctionSignature, FunctionParameter

if TYPE_CHECKING:
    from mcscript.lang.resource.base.ResourceBase import Resource
    from mcscript.compiler.CompileState import CompileState

    MacroCallable = Callable[[CompileState], Resource]


def include() -> List[MacroResource]:
    from mcscript.lang.std import builtins
    return builtins.include()


def macro(*, parameters: List[FunctionParameter] = None, return_type: Type = Null,
          name: str = None, documentation: str = None) -> Callable[[MacroCallable], MacroResource]:
    """
    Returns a MacroResource object wrapping this function
    If a signature is specified, all parameters will be matched first and the function
    is guaranteed to only get parameters of the correct type.
    If a name is specified, the default name (name of the function) will be overwritten.
    If a docstring is specified, the fun.__doc__ attribute will not be used.

    Args:
        parameters: The function parameters. Default to arbitrary amount of any resource
        return_type: The type of resource returned by this macro. Default to NullResource
        name: The name of this macro
        documentation: The documentation

    Returns:
        A Function taking a function, which returns a MacroResource object
    """

    def wrapper(func: MacroCallable) -> MacroResource:
        nonlocal name, parameters
        name = name or func.__name__
        doc = documentation or func.__doc__
        parameters = parameters or [
            FunctionParameter("parameters", Any, FunctionParameter.ParameterCount.ARBITRARY)
        ]
        return MacroResource(
            FunctionSignature(
                parameters,
                return_type,
                name,
                documentation=doc
            ),
            name,
            func,
        )

    return wrapper
