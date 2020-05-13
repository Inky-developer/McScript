from __future__ import annotations

from typing import TYPE_CHECKING, Union

from lark import Token, Tree

from mcscript.exceptions.McScriptException import McScriptException
from mcscript.exceptions.utils.sourceAnnotation import SourceAnnotation, SourceAnnotationList

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState
    from mcscript.lang.resource.base.ResourceBase import Resource


class McScriptError(McScriptException):
    """ base McScript error"""

    def __init__(self, message, compileState: CompileState, *source_annotations: SourceAnnotation, showErr=True):
        tree = compileState.currentTree
        if tree is not None:
            header = f"At line {tree.line} column {tree.column}\n"
            msg = SourceAnnotationList()
            if showErr:
                msg += SourceAnnotation.from_token(compileState.code, tree, message)
            else:
                msg += message

            # if custom annotations specified, include them and sort everything by line numbers
            if source_annotations:
                msg += SourceAnnotationList(*source_annotations)
                msg = msg.sorted()

            msg = header + str(msg)
        else:
            msg = message
        super().__init__(msg)
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

    def __init__(self, message: str, token: Union[Token, Tree], compileState: CompileState):
        super().__init__(
            message,
            compileState,
            SourceAnnotation.from_token(compileState.code, token, "Variable statically defined here")
        )


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


class McScriptIndexError(McScriptError):
    """
    Thrown when an invalid index of a sequence is accessed
    """

    def __init__(self, index: int, compileState: CompileState, maxIndex: int = None, customMessage: str = ""):
        if maxIndex is not None:
            if maxIndex > 0:
                message = f"Trying to access index {index}, while the maximum allowed index is {maxIndex}."
            else:
                message = f"Trying access element on an empty array"
        else:
            message = f"Invalid index: {index}"
        if customMessage:
            message += "\n" + customMessage
        super().__init__(message, compileState)


class McScriptDeclarationError(McScriptError):
    """
    Thrown when a variable is declared in an invalid way
    """


class McScriptInvalidMarkupError(McScriptError):
    """
    Thrown when the user has entered invalid markup (which could not be parsed)
    """


class McScriptChangedTypeError(McScriptError):
    def __init__(self, identifier: str, value: Resource, compileState: CompileState):
        var = compileState.currentNamespace().getVariableInfo(compileState, identifier)
        resource = compileState.currentNamespace()[identifier]

        # if the user tries to overwrite a builtin, the first message does not make sense
        if identifier in compileState.stack.stack[0]:
            message = SourceAnnotation.from_token(
                compileState.code,
                compileState.currentTree,
                f"Trying to change the type of built-in resource {identifier} "
                f"from {resource.type().value} to {value.type().value}"
            )
        else:
            message = SourceAnnotation.from_token(
                compileState.code,
                var.declaration,
                f"Variable {identifier} declared with type {resource.type().value}"
            ) + SourceAnnotation.from_token(
                compileState.code,
                compileState.currentTree,
                f"Trying to change type of {identifier} to {value.type().value}"
            )
        super().__init__(str(message), compileState, False)


class McScriptUnexpectedTypeError(McScriptError):
    def __init__(self, expected_type, got_type, compileState: CompileState):
        if hasattr(expected_type, "type") and callable(expected_type.type):
            expected_type = expected_type.type().value
        if hasattr(got_type, "type") and callable(got_type.type):
            got_type = got_type.type().value
        super().__init__(f"Expected type {expected_type} but got type {got_type}", compileState)
