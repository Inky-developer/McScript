from __future__ import annotations

from abc import ABC, abstractmethod
from inspect import isabstract
from typing import TYPE_CHECKING, Type

from src.mcscript.Exceptions import McScriptNameError
from src.mcscript.lang.Resource.ResourceType import ResourceType

if TYPE_CHECKING:
    from src.mcscript.lang.Resource.AddressResource import AddressResource
    from src.mcscript.lang.Resource.FixedNumberResource import FixedNumberResource
    from src.mcscript.lang.Resource.NumberResource import NumberResource
    from src.mcscript.compiler.CompileState import CompileState


class Resource(ABC):
    _reference = {}
    isDefault = True

    def __init_subclass__(cls, **kwargs):
        if not isabstract(cls):
            if cls.type() in Resource._reference:
                if Resource._reference[cls.type()].isDefault and cls.isDefault:
                    raise ReferenceError(f"Multiple resources of type {cls.type().name} register as default.")
                if not cls.isDefault:
                    return
            Resource._reference[cls.type()] = cls

    def convertToNumber(self, compileState: CompileState) -> NumberResource:
        """ Convert this to a number resource"""
        raise TypeError(f"{repr(self)} cannot be converted to a number.")

    def convertToFixedNumber(self, compileState: CompileState) -> FixedNumberResource:
        """ Convert this resource to a fixed point number"""
        raise TypeError(f"{repr(self)} cannot be converted to a fixed point number.")

    @classmethod
    def getResourceClass(cls, resourceType: ResourceType) -> Type[Resource]:
        return cls._reference[resourceType]

    @staticmethod
    @abstractmethod
    def type() -> ResourceType:
        """ return the type of resource that is represented by this object"""

    @abstractmethod
    def toNumber(self) -> int:
        """ This Resource as a number. If not supported raise a TypeError."""

    @abstractmethod
    def toString(self) -> str:
        """ This Resource as a string. If not supported raise a TypeError"""


class ValueResource(Resource, ABC):
    """
    Used for atomics in the build process
    """

    # whether this resource has a static value like a number - False for AddressResource
    _hasStaticValue = True

    def __init__(self, value, isStatic):
        self.value = None
        self.isStatic = False
        self.setValue(value, isStatic)

    @property
    def hasStaticValue(self):
        return self.isStatic and self._hasStaticValue

    def load(self, compileState: CompileState) -> Resource:
        """
        Default: just return this and do nothing
        loads this resource. A NumberVariableResource would load to a scoreboard, A StringResource would check
        for variables.
        :param compileState: the compile state
        :return: self
        """
        return self

    def storeToNbt(self, stack: AddressResource, compileState: CompileState) -> ValueResource:
        """
        Called when this resource should be stored in a variable
        stores this variable to nbt.
        :param stack:
        :param compileState:
        :return:
        """
        raise TypeError(f"{repr(self)} does not support this operation")

    def setValue(self, value, isStatic: bool):
        self.value = value
        self.isStatic = isStatic
        if self.isStatic and not self.typeCheck():
            raise ValueError(f"Invalid value for {repr(self)}: " + repr(value))

    def toNumber(self) -> int:
        value = self.embed()
        try:
            return int(value)
        except ValueError:
            raise TypeError

    def toString(self) -> str:
        return self.embed()

    @abstractmethod
    def embed(self) -> str:
        """ return a string that can be embedded into a mc function"""

    @abstractmethod
    def typeCheck(self) -> bool:
        """ return whether this is a legal value for this Resource"""

    def __eq__(self, other):
        return self.value == other.value

    def __hash__(self):
        return hash(self.value)

    def __str__(self):
        return self.toString()

    def __repr__(self):
        return f"{self.type().name}({self.toString()})"

    def __int__(self):
        return self.toNumber()


class ObjectResource(Resource, ABC):
    def __init__(self):
        self.namespace = {}

    def getAttribute(self, name: str) -> Resource:
        """
        Returns the attribute with the given name
        @raises: McScriptNameError when the property does not exist
        """
        raise McScriptNameError(f"Property {name} does not exist for {type(self)}.")

    def __repr__(self):
        return f"Object {type(self).__name__}"
