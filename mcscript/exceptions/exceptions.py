from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Any

from mcscript.exceptions.McScriptException import McScriptError

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class McScriptEnumValueAlreadyDefinedError(McScriptError):
    def __init__(self, enum: str, value: str, compile_state: CompileState):
        super().__init__(f"{value} was already defined for enum {enum}", compile_state)


class McScriptUnexpectedTypeError(McScriptError):
    def __init__(self, name: str, got: Any, expected: Any, compile_state: CompileState):
        super().__init__(f"Unexpected type for {name}: Got {got}, but expected {expected}", compile_state)


class McScriptUnsupportedOperationError(McScriptError):
    def __init__(self, operation: str, a: Optional[Any], b: Optional[Any], compile_state: CompileState):
        if a is None and b is None:
            msg = f"The operation '{operation}' is not supported"
        elif a is not None and b is None:
            msg = f"The operation '{operation}' is not supported on {a}"
        elif a is not None and b is not None:
            msg = f"The operation '{operation}' is not supported between {a} and {b}"
        else:
            msg = f"The operation '{operation}' is not supported"
        super().__init__(msg, compile_state)


class McScriptDeclarationError(McScriptError):
    def __init__(self, msg: str, compile_state: CompileState):
        super().__init__(msg, compile_state)


class McScriptArgumentError(McScriptError):
    def __init__(self, msg: str, compile_state: CompileState):
        super().__init__(msg, compile_state)


class McScriptInvalidSelectorError(McScriptError):
    def __init__(self, msg: str, compile_state: CompileState):
        super().__init__(msg, compile_state)


class McScriptUndefinedVariableError(McScriptError):
    def __init__(self, var_name: str, compile_state: CompileState):
        super().__init__(f"The variable {var_name} is not defined", compile_state)


class McScriptUndefinedAttributeError(McScriptError):
    def __init__(self, base_obj: Any, attribute: str, compile_state: CompileState):
        super().__init__(f"{base_obj} has not attribute '{attribute}'", compile_state)


class McScriptValueError(McScriptError):
    def __init__(self, got: Any, expected: Any, compile_state):
        if isinstance(expected, (tuple, list)):
            msg = f"Expected on of {expected}"
        else:
            msg = f"Expected {expected}"
        super().__init__(f"Unexpected value '{got}': {msg}", compile_state)


class McScriptInvalidMarkupError(McScriptError):
    def __init__(self, msg: str, compile_state: CompileState):
        super().__init__(msg, compile_state)


class McScriptOutOfBoundsError(McScriptError):
    def __init__(self, value: int, max_value: int, compile_state: CompileState):
        super().__init__(f"Index out of bounds. Maximum allowed index is {max_value}, got {value}", compile_state)


class McScriptIfElseReturnTypeError(McScriptError):
    def __init__(self, got: Any, compile_state: CompileState):
        super().__init__(f"An if-else expression can only return atomic values, got {got}", compile_state)
