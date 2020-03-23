
class McScriptError(Exception):
    """ base McScript error"""

    def __init__(self, message, token=None):
        if token:
            message = f"At line {token.line} column {token.column}: {message}"
        super().__init__(message)
        self.token = token


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
