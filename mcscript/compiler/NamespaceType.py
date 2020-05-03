from enum import Enum, auto


class NamespaceType(Enum):
    """
    Each namespace can have a different type. The global namespace will have type GLOBAL, a namespace for a struct would
    have STRUCT.
    A namespace type is considered to have a static context if it is possible to know exactly how often the code
    is going to be executed at compile time.
    """
    GLOBAL = auto(), True
    FUNCTION = auto(), False
    INLINE_FUNCTION = auto(), True
    STRUCT = auto(), True
    METHOD = auto(), True
    BLOCK = auto(), True
    CONTEXT_MANIPULATOR = auto(), False
    CONDITIONAL = auto(), False
    LOOP = auto(), False
    UNROLLED_LOOP = auto(), True

    def __new__(cls, value: int, staticContext: bool):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.hasStaticContext = staticContext
        return obj
