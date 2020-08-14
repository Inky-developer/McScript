"""
Defines all atomic types

The atomic types are:
    - Int
    - Fixed
    - String
    - Null
    - Bool
    - Selector
    - Function
    - Type (the type of a type)
    - Tuple
    - List
    - Enum
    - Iterator
    - Struct
    - Object (custom type)

Todo: Implement the additional types Any and Number
"""
from mcscript.lang.Type import Type

# The index for atomic types is counted down and the index for struct types is counted up from zero

index = -2

# The base type. All other types are subtypes of this
Any = Type(-1, "Any", set())


def _make_type(name: str) -> Type:
    global index
    t = Type(index, name, {Any})
    index -= 1
    return t


Int = _make_type("Int")
Fixed = _make_type("Fixed")
String = _make_type("String")
Null = _make_type("Null")
Bool = _make_type("Bool")
Selector = _make_type("Selector")
Function = _make_type("Function")
MetaType = _make_type("Type")
Tuple = _make_type("Tuple")
List = _make_type("List")
Enum = _make_type("Enum")
Iterator = _make_type("Iterator")
Struct = _make_type("Struct")

# All types, keyed by their mcscript name
ATOMIC_TYPES = {val.name: val for val in globals().values() if isinstance(val, Type)}
