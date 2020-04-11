from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.Exceptions.McScriptException import McScriptException

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class McScriptError(McScriptException):
    """ base McScript error"""

    def __init__(self, message, compileState: CompileState):
        tree = compileState.currentTree
        if tree:
            code = compileState.code[tree.line - 1]
            message = f"At line {tree.line} column {tree.column}\n" \
                      f"{code}\n" \
                      f"{' ' * max(tree.column - 1, 0)}{'^' * max(tree.end_column - tree.column, 0)}\n" \
                      f"{message}"
        super().__init__(message)
        self.tree = tree


class McScriptNotImplementError(McScriptError):
    """
    thrown when something is not yet implemented
    """


class McScriptNameError(McScriptError):
    """
    Describes an error while trying to access a variable. Can be thrown when a variable is not defined
    or when a property of an object does not exist.
    """


class McScriptArgumentsError(McScriptError):
    """
    Thrown when there is an arguments mismatch while calling a function
    """


class McScriptNotStaticError(McScriptError):
    """
    Thrown when a const declaration is not possible because the value is not known at compile-time
    """


class McScriptIsStaticError(McScriptError):
    """
    Thrown when a static value is found in the wrong place
    """


class McScriptTypeError(McScriptError):
    """
    Thrown when another type than expected was found
    """


class McScriptSyntaxError(McScriptError):
    """
    Thrown when invalid syntax is found that can not be validated using the grammar
    """


class McScriptAttributeError(McScriptError):
    """
    Thrown when an invalid property of an object is accessed
    """
