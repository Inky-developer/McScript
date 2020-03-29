from __future__ import annotations

from abc import ABC, abstractmethod
from inspect import isabstract
from typing import TYPE_CHECKING, Type

from src.mcscript.Exceptions import McScriptNameError
from src.mcscript.compiler.NamespaceType import NamespaceType
from src.mcscript.lang.Resource.ResourceType import ResourceType

if TYPE_CHECKING:
    from src.mcscript.lang.Resource.NbtAddressResource import NbtAddressResource
    from src.mcscript.lang.Resource.FixedNumberResource import FixedNumberResource
    from src.mcscript.lang.Resource.NumberResource import NumberResource
    from src.mcscript.lang.Resource.BooleanResource import BooleanResource
    from src.mcscript.compiler.CompileState import CompileState


class Resource(ABC):
    _reference = {}
    isDefault: bool = True
    """
    whether this class is the default implementation of all resources that have the same ResourceType.
    """

    requiresInlineFunc: bool = True
    """ 
    whether this resource class requires an inline function to be used as a function parameters.
    Should be True if this is a complex resource (stores multiple other resources like a struct) or if it cannot be
    stored in minecraft (like a selector)
    when this is set to False, an implementation of createEmptyResource is required.
    """

    def __init_subclass__(cls, **kwargs):
        if not isabstract(cls):
            if cls.type() in Resource._reference:
                if Resource._reference[cls.type()].isDefault and cls.isDefault:
                    raise ReferenceError(f"Multiple resources of type {cls.type().name} register as default.")
                if not cls.isDefault:
                    return

            # implementation validity checks
            if not cls.requiresInlineFunc and (
                    cls.createEmptyResource.__func__ == Resource.createEmptyResource.__func__ or
                    cls.copy == Resource.copy
            ):
                raise NotImplementedError(
                    F"every subclass of Resource that does not require an inline function "
                    F"must implement 'createEmptyResource' and 'copy', {cls.__name__} does not."
                )
            Resource._reference[cls.type()] = cls

    def convertToNumber(self, compileState: CompileState) -> NumberResource:
        """ Convert this to a number resource"""
        raise TypeError(f"{repr(self)} cannot be converted to a number.")

    def convertToFixedNumber(self, compileState: CompileState) -> FixedNumberResource:
        """ Convert this resource to a fixed point number"""
        raise TypeError(f"{repr(self)} cannot be converted to a fixed point number.")

    def convertToBoolean(self, compileState: CompileState) -> BooleanResource:
        """ Convert this resource to a boolean resource"""
        raise TypeError(f"{repr(self)} cannot be converted to a boolean.")

    def load(self, compileState: CompileState, stack: ValueResource = None) -> Resource:
        """
        Default: just return this and do nothing
        loads this resource. A NumberVariableResource would load to a scoreboard, A StringResource would check
        for variables.
        :param compileState: the compile state
        :param stack: an optional stack to load this variable to
        :return: self
        """
        return self

    def storeToNbt(self, stack: NbtAddressResource, compileState: CompileState) -> Resource:
        """
        Called when this resource should be stored in a variable
        stores this variable to nbt.
        :param stack:
        :param compileState:
        :return:
        """
        raise TypeError(f"{repr(self)} does not support this operation")

    def copy(self, target: ValueResource, compileState: CompileState) -> Resource:
        """
        Non-static operation. Must be implemented if this resource does not require inline-functions.
        Move the value of this resource to the target resource and return the new resource
        Default implementation raises TypeError
        :param target: the target resource one of AddressResource and NbtAddressResource
        :param compileState: the compile state
        :return: the new resource
        """
        raise TypeError

    # operations that can be performed on a resource
    # include addition, subtraction, multiplication, division, unary operators -, --, ++
    def numericOperation(self, other: ValueResource, operator: BinaryOperator, compileState: CompileState) -> Resource:
        from src.mcscript.data.Commands import BinaryOperator
        other = self.checkOtherOperator(other, compileState)
        try:
            if operator == BinaryOperator.PLUS:
                return self.operation_plus(other, compileState)
            elif operator == BinaryOperator.MINUS:
                return self.operation_minus(other, compileState)
            elif operator == BinaryOperator.TIMES:
                return self.operation_times(other, compileState)
            elif operator == BinaryOperator.DIVIDE:
                return self.operation_divide(other, compileState)
            elif operator == BinaryOperator.MODULO:
                return self.operation_modulo(other, compileState)
        except TypeError:
            raise McScriptTypeError(f"{repr(self)} does not support the binary operation {operator.name}")
        raise ValueError("Unknown operator: " + repr(operator))

    def checkOtherOperator(self, other: ValueResource, compileState: CompileState) -> ValueResource:
        """
        Called before an operation to convert the operator to a more fitting type
        :param other: the other value
        :param compileState: the compile state
        """
        return other

    def operation_plus(self, other: ValueResource, compileState: CompileState) -> ValueResource:
        raise TypeError

    def operation_minus(self, other: ValueResource, compileState: CompileState) -> ValueResource:
        raise TypeError

    def operation_times(self, other: ValueResource, compileState: CompileState) -> ValueResource:
        raise TypeError

    def operation_divide(self, other: ValueResource, compileState: CompileState) -> ValueResource:
        raise TypeError

    def operation_modulo(self, other: ValueResource, compileState: CompileState) -> ValueResource:
        raise TypeError

    def operation_negate(self, compileState: CompileState) -> Resource:
        """
        Returns a resource whose value negated is the value of this resource
        :param compileState: the compileState
        :return: the new resource
        """
        raise TypeError

    def operation_increment_one(self, compileState: CompileState) -> Resource:
        """
        Returns a resource which has the value +1 of this resource
        :param compileState: the compileState
        :return: the new resource
        """
        raise TypeError

    def operation_decrement_one(self, compileState: CompileState) -> Resource:
        """
        Returns a resource which has the value of -1 of this resource
        :param compileState: the compileState
        :return: the new resource
        """
        raise TypeError

    def operation_call(self, compileState: CompileState, *parameters: Resource,
                       **keywordParameters: Resource) -> Resource:
        """
        If this method is implemented, the resource can be treated like a function
        :param compileState: the compile state
        :param parameters: a list of parameters
        :param keywordParameters: a list of keyword parameters, currently they are not yet supported
        :return: a new resource
        """
        raise TypeError

    @classmethod
    def getResourceClass(cls, resourceType: ResourceType) -> Type[Resource]:
        return cls._reference[resourceType]

    @classmethod
    def createEmptyResource(cls, identifier: str, compileState: CompileState) -> Resource:
        """
        Creates an empty resources which is not static and has static address assigned to it.
        This is used in not-inline functions to generate the function before it is called
        :param identifier: the identifier of the resource in the code
        :param compileState: the compile state
        :return: the generated resource
        :raises TypeError: if this operation is not supported by this class (default implementation)
        """
        raise TypeError

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
    def __init__(self, namespace: Namespace = None):
        from src.mcscript.compiler.Namespace import Namespace
        # ToDo: is this correct?
        self.namespace = namespace or Namespace(namespaceType=NamespaceType.STRUCT)

    def getAttribute(self, name: str) -> Resource:
        """
        Returns the attribute with the given name
        @raises: McScriptNameError when the property does not exist
        """
        raise McScriptNameError(f"Property {name} does not exist for {type(self)}.")

    def setAttribute(self, compileState: CompileState, name: str, value: Resource) -> Resource:
        self.namespace[name] = value
        return value

    def __repr__(self):
        return f"Object {type(self).__name__}"
