from enum import Enum, auto


class NamespaceType(Enum):
    """
    Each namespace can have a different type. The global namespace will have type GLOBAL, a namespace for a struct would
    have STRUCT.
    """
    GLOBAL = auto()
    FUNCTION = auto()
    STRUCT = auto()
    METHOD = auto()
    BLOCK = auto()
    LOOP = auto()
    OTHER = auto()
