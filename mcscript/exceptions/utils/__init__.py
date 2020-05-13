def requireType(obj, type_, compileState):
    """Requires obj to be of the same type as `type`. Raise if that is not the case."""
    from mcscript.exceptions.compileExceptions import McScriptUnexpectedTypeError
    from mcscript.lang.utility import compareTypes
    if not compareTypes(obj, type_):
        raise McScriptUnexpectedTypeError(type_, obj, compileState)
