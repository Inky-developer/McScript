from enum import Enum, auto


class ContextType(Enum):
    """
    Stores the type of context and whether it is static or dynamic
    """

    # The global context is very simple, static evaluating generally possible
    GLOBAL = auto(), True

    # Non-inline function. Dynamic since nothing about call-time known
    FUNCTION = auto(), False

    # Compile every time called, so static
    INLINE_FUNCTION = auto(), True

    # The body of a struct definition
    STRUCT = auto(), True

    # An implicit inline function in struct bodies
    METHOD = auto(), True

    # Context in a procedural macro, like a builtin function, basically no side-effects
    MACRO = auto(), True

    # Will eventually not be used any more. used to describe the body of if statements and while loops
    BLOCK = auto(), True

    # It can't be known for what entities this will execute, so dynamic
    CONTEXT_MANIPULATOR = auto(), False

    # If statement, if it can be evaluated at compile time no body namespace necessary
    CONDITIONAL = auto(), False

    # A while or a do-while loop
    LOOP = auto(), False

    # A static loop, for example iteration over a tuple
    UNROLLED_LOOP = auto(), True

    def __new__(cls, value: int, staticContext: bool):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.hasStaticContext = staticContext
        return obj
