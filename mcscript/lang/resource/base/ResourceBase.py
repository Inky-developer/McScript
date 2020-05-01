from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum, auto
from inspect import isabstract
from typing import Dict, List, TYPE_CHECKING, Type, Union

from lark import Tree

from mcscript.Exceptions.compileExceptions import McScriptTypeError
from mcscript.compiler.Namespace import NamespaceType
from mcscript.data.commands import BinaryOperator, ConditionalExecute, Relation
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.utils.JsonTextFormat.ResourceTextFormatter import ResourceTextFormatter
    from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
    from mcscript.lang.resource.FixedNumberResource import FixedNumberResource
    from mcscript.lang.resource.NumberResource import NumberResource
    from mcscript.lang.resource.BooleanResource import BooleanResource
    from mcscript.compiler.CompileState import CompileState
    from mcscript.compiler.Namespace import Namespace


class MinecraftDataStorage(Enum):
    SCOREBOARD = auto()
    STORAGE = auto()
    NONE = auto()


class Resource(ABC):
    _reference = {}
    _reference_variables = {}
    isDefault: bool = True
    isVariable: bool = False
    """
    whether this class is the default implementation of all resources that have the same ResourceType.
    """

    storage: MinecraftDataStorage = MinecraftDataStorage.NONE

    requiresInlineFunc: bool = True
    """ 
    whether this resource class requires an inline function to be used as a function parameters.
    Should be True if this is a complex resource (stores multiple other resources like a struct) or if it cannot be
    stored in minecraft (like a selector)
    when this is set to False, an implementation of createEmptyResource is required.
    """

    # noinspection PyUnresolvedReferences
    def __init_subclass__(cls, **kwargs):
        if not isabstract(cls):
            # implementation validity checks
            if not cls.requiresInlineFunc and (
                    cls.createEmptyResource.__func__ == Resource.createEmptyResource.__func__ or
                    cls.copy == Resource.copy
            ):
                raise NotImplementedError(
                    F"every subclass of resource that does not require an inline function "
                    F"must implement 'createEmptyResource' and 'copy', {cls.__name__} does not."
                )
            if cls.isDefault or cls.type() not in Resource._reference:
                if cls.type() in Resource._reference and Resource._reference[cls.type()].isDefault and cls.isDefault:
                    raise ReferenceError(f"Multiple resources of type {cls.type().name} register as default.")
                if cls.type() not in Resource._reference or not Resource._reference[cls.type()].isDefault:
                    Resource._reference[cls.type()] = cls

            if cls.type() in Resource._reference_variables and cls.isVariable:
                raise ReferenceError("Multiple resources of type {cls.type().name} register as variable.")

            if cls.isVariable:
                Resource._reference_variables[cls.type()] = cls

    def toTextJson(self, compileState: CompileState, formatter: ResourceTextFormatter) -> Union[Dict, List]:
        """
        Creates a string that can be used as a minecraft tellraw or title string.

        Args:
            compileState: the compile state
            formatter: A formatter that can be used to format this resource

        Returns:
            A dictionary

        Raises:
            TypeError: if this method should not be called.
        """
        raise TypeError()

    def allow_redefine(self, compileState) -> bool:
        """
        This method is called when a resource that has been defined previously with the same name should be redefined.
        The default implementation allows this but some resources, which must handle these operations statically,
        have to prohibit this behaviour.

        Args:
            compileState: the compile state

        Returns:
            Whether to allow a redefinition of this resource.
        """
        return True

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

        Args:
            compileState: the compile state
            stack: an optional stack to load this variable to
        """
        return self

    def storeToNbt(self, stack: NbtAddressResource, compileState: CompileState) -> Resource:
        """
        Called when this resource should be stored in a variable
        stores this variable to nbt.

        Args:
            stack: the stack on the data storage this resource should be stored to
            compileState: the Compile state
        """
        raise TypeError(f"{repr(self)} does not support this operation")

    def copy(self, target: ValueResource, compileState: CompileState) -> Resource:
        """
        Non-static operation. Must be implemented if this resource does not require inline-functions.
        Move the value of this resource to the target resource and return the new resource
        Default implementation raises TypeError

        Args:
            target: the target resource one of AddressResource and NbtAddressResource
            compileState: the compile state

        Returns:
            the new resource
        """
        raise TypeError

    def getAttribute(self, compileState: CompileState, name: str) -> Resource:
        """
        Returns the attribute with `name`.

        This is usually invoked by ``a.dot.between.objects``

        Args:
            compileState: the compile state
            name: the name

        Returns:
            the resource

        Raises:
            TypeError: if the operation is not supported
        """
        raise TypeError()

    def setAttribute(self, compileState: CompileState, name: str, value: Resource):
        """
        Sets the attribute with name `name`.

        Args:
            compileState: the compile state
            name: the name
            value: the value

        Raises:
            TypeError: if the operation is not supported
        """
        raise TypeError()

    def iterate(self, compileState: CompileState, varName: str, block: Tree):
        """
        If this resource supports iterations, this method is called to iterate over.

        it is expected that `block` is execute for every element.
        `varName` should have the value of each element, respectively.

        It may be used a recursive function loop to iterate over the elements or just an "unrolled" loop if the
        number of elements is known at compile time.

        Args:
            compileState: the compile state
            varName: the name of the iteration variable
            block: the tree that is the loop body

        Raises:
            TypeError: if this operation is not supported
        """
        raise TypeError

    # operations that can be performed on a resource
    # include addition, subtraction, multiplication, division, unary operators -, --, ++
    def numericOperation(self, other: ValueResource, operator: BinaryOperator, compileState: CompileState) -> Resource:
        from mcscript.data.commands import BinaryOperator
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
            raise McScriptTypeError(f"{repr(self)} does not support the binary operation {operator.name}", compileState)
        raise ValueError("Unknown operator: " + repr(operator))

    def checkOtherOperator(self, other: ValueResource, compileState: CompileState) -> ValueResource:
        """
        Called before an operation to convert the operator to a more fitting type

        Args:
            other: the other value
            compileState: the compile state
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

        Args:
            compileState: the compileState

        Returns:
            the new resource
        """
        raise TypeError

    def operation_test_relation(self, compileState: CompileState, relation: Relation,
                                other: Resource) -> ConditionalExecute:
        """
        Checks if the `relation` evaluates to true for both resources

        Args:
            compileState: the compile state
            relation: the relation. can be ==, !=, >, <, >=, <=
            other: the other resource

        Returns:
            A conditional execute that runs if the relations matches both resources
        """
        raise TypeError

    def operation_increment_one(self, compileState: CompileState) -> Resource:
        """
        Returns a resource which has the value +1 of this resource

        Args:
            compileState: the compileState

        Returns:
            the new resource
        """
        raise TypeError

    def operation_decrement_one(self, compileState: CompileState) -> Resource:
        """
        Returns a resource which has the value of -1 of this resource

        Args:
            compileState: the compileState

        Returns:
            the new resource
        """
        raise TypeError

    def operation_call(self, compileState: CompileState, *parameters: Resource,
                       **keywordParameters: Resource) -> Resource:
        """
        If this method is implemented, the resource can be treated like a function

        Args:
            compileState: the compile state
            parameters: a list of parameters
            keywordParameters: a list of keyword parameters, currently they are not yet supported

        Returns:
            a new resource
        """
        raise TypeError

    def operation_get_element(self, compileState: CompileState, index: Resource) -> Resource:
        """
        If this resource supports array-like operations, this method should be implemented.

        Accesses the element `index` of this resource

        Args:
            compileState: the compile state
            index: a resource that can be converted to an integer

        Returns:
            the element at the index

        Raises:
            TypeError: if this operation is not supported
            McScriptIndexError: if the index is invalid
        """
        raise TypeError()

    def operation_set_element(self, compileState: CompileState, index: Resource, value: Resource):
        """
        If this resource supports array-like operations, this method should be implemented.

        Sets the resource ´value´ at the index ´index´

        Args:
            compileState: the compile state
            index: a resource that can be converted to an integer
            value: any resource

        Raises:
            NotImplementedError: if this operation is not supported
            TypeError: if the index is invalid
        """
        raise TypeError()

    @classmethod
    def getResourceClass(cls, resourceType: ResourceType) -> Type[Resource]:
        if resourceType == ResourceType.RESOURCE:
            return Resource
        elif resourceType == ResourceType.VALUE_RESOURCE:
            return ValueResource

        return cls._reference[resourceType]

    @classmethod
    def getVariableResourceClass(cls, resourceType: ResourceType) -> Type[Resource]:
        return cls._reference_variables[resourceType]

    @classmethod
    def createEmptyResource(cls, identifier: str, compileState: CompileState) -> Resource:
        """
        Creates an empty resources which is not static and has static address assigned to it.
        This is used in not-inline functions to generate the function before it is called

        Args:
            identifier: the identifier of the resource in the code
            compileState: the compile state
            the generated resource

        Raises:
            TypeError: if this operation is not supported by this class (default implementation)
        """
        raise TypeError

    @staticmethod
    def type() -> ResourceType:
        """ return the type of resource that is represented by this object"""
        return ResourceType.RESOURCE

    @abstractmethod
    def toNumber(self) -> int:
        """ This resource as a number. If not supported raise a TypeError."""

    @abstractmethod
    def toString(self) -> str:
        """ This resource as a string. If not supported raise a TypeError"""


class ValueResource(Resource, ABC):
    """
    Used for atomics in the build process
    """

    # whether this resource has a static value like a number - False for AddressResource
    _hasStaticValue = True

    storage = MinecraftDataStorage.SCOREBOARD

    def __init__(self, value, isStatic):
        super().__init__()
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

    def copyUnlessStatic(self, target: ValueResource, compileState: CompileState):
        return self if self.isStatic else self.copy(target, compileState)

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.VALUE_RESOURCE

    @abstractmethod
    def embed(self) -> str:
        """ return a string that can be embedded into a mc function"""

    @abstractmethod
    def typeCheck(self) -> bool:
        """ return whether this is a legal value for this resource"""

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.value == other.value

    def __hash__(self):
        return hash(self.value)

    def __str__(self):
        return self.toString()

    def __repr__(self):
        return f"{self.type().name}({self.toString()})"

    def __int__(self):
        return self.toNumber()


class ObjectResource(Resource, ABC):
    storage = MinecraftDataStorage.STORAGE

    def __init__(self, namespace: Namespace = None):
        super().__init__()
        from mcscript.compiler.Namespace import Namespace
        self.namespace = namespace or Namespace(0, NamespaceType.STRUCT)

    @staticmethod
    @abstractmethod
    def type() -> ResourceType:
        pass

    def allow_redefine(self, compileState) -> bool:
        return compileState.currentNamespace().isContextStatic()

    def getBasePath(self) -> NbtAddressResource:
        """ Returns the base path which contains the attributes of this object. """
        raise TypeError

    def getAttribute(self, compileState: CompileState, name: str) -> Resource:
        if name not in self.namespace:
            raise AttributeError(f"Property {name} does not exist for {type(self)}.")
        return self.namespace[name]

    def setAttribute(self, compileState: CompileState, name: str, value: Resource) -> Resource:
        self.namespace[name] = value
        return value

    def __repr__(self):
        return f"Object {type(self).__name__}"
