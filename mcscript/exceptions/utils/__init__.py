from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState
    from mcscript.lang.Type import Type
    from mcscript.lang.resource.base.ResourceBase import Resource


def requireType(obj: Resource, rtype: Type, compileState: CompileState):
    """Requires obj to be of the same type as `type`. Raise if that is not the case."""
    from mcscript.exceptions.compileExceptions import McScriptUnexpectedTypeError
    if not obj.type().matches(rtype):
        raise McScriptUnexpectedTypeError(rtype, obj, compileState)
