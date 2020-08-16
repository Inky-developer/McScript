from __future__ import annotations

from typing import Set


class Type:
    """
    Generic type class.
    Types are used to design safe apis for functions and structs.


    ToDo: refine the type class to support generic types and traits
    """
    __slots__ = ("uid", "name", "bases")

    def __init__(self, uid: int, name: str, bases: Set[Type]):
        self.uid = uid
        self.name = name
        self.bases = bases

    def is_same_type(self, other: Type) -> bool:
        return other.uid == self.uid

    def matches(self, other: Type) -> bool:
        """
        Whether this type "matches" the other type, ie. whether both are the same type or
        the other type is more general than this type.

        Int matches on Number, Number matches on Number, but Number does not match on Int

        Args:
            other: the other type

        Returns:
            Whether self matches on the other type
        """
        return self.is_same_type(other) or any(i.is_same_type(other) for i in self.bases)

    def __repr__(self) -> str:
        return f"Type(uid: {self.uid}, name: {self.name}, bases: {self.bases})"

    def __str__(self) -> str:
        return f"{{{self.name}}}"

    def __eq__(self, other: Type) -> bool:
        if not isinstance(other, Type):
            raise NotADirectoryError
        return self.is_same_type(other)

    def __hash__(self) -> int:
        return hash(self.uid)
