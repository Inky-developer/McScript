from __future__ import annotations

from abc import ABC, abstractmethod, abstractstaticmethod
from enum import Enum, auto
from inspect import isabstract
from typing import (TYPE_CHECKING, Any, ClassVar, Dict, List, Optional, Type,
                    Union, TypeVar, Generic)

from lark import Tree

from mcscript.analyzer.VariableContext import VariableContext
from mcscript.compiler.ContextType import ContextType
from mcscript.exceptions.compileExceptions import McScriptTypeError
from mcscript.ir.command_components import BinaryOperator
from mcscript.lang.resource import import_sub_modules
from mcscript.lang.resource.base.ResourceType import ResourceType
from mcscript.utils.resources import ScoreboardValue
from mcscript.utils.JsonTextFormat.objectFormatter import format_score, format_text

if TYPE_CHECKING:
    from mcscript.compiler.Context import Context
    from mcscript.ir.command_components import ScoreRelation
    from mcscript.ir.components import ConditionalNode
    from mcscript.utils.JsonTextFormat.ResourceTextFormatter import ResourceTextFormatter
    from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
    from mcscript.lang.resource.FixedNumberResource import FixedNumberResource
    from mcscript.lang.resource.NumberResource import NumberResource
    from mcscript.lang.resource.BooleanResource import BooleanResource
    from mcscript.compiler.CompileState import CompileState


class MinecraftDataStorage(Enum):
    SCOREBOARD = auto()
    STORAGE = auto()
    NONE = auto()


class Resource(ABC):
    _reference: ClassVar[Dict] = {}
    _reference_variables: ClassVar[Dict] = {}

    # ToDo clean up the isDefault / isVariable mess
    isDefault: ClassVar[bool] = True

    isVariable: ClassVar[bool] = False
    """
    whether this class is the default implementation of all resources that have the same ResourceType.
    """

    storage: ClassVar[MinecraftDataStorage] = MinecraftDataStorage.NONE
    """
    How this resource is stored in minecraft
    """

    requiresInlineFunc: ClassVar[bool] = True
    """ 
    whether this resource class requires an inline function to be used as a function parameters.
    Should be True if this is a complex resource (stores multiple other resources like a struct) or if it cannot be
    stored in minecraft (like a selector)
    when this is set to False, an implementation of createEmptyResource is required.
    """

    # ToDo wtf is this
    _context: Optional[VariableContext]
    """
    If this resource directly corresponds to a variable, this field will contain its context.
    """

    # noinspection PyUnresolvedReferences
    def __init_subclass__(cls, **kwargs):
        if not isabstract(cls):
            # implementation validity checks
            if cls.isDefault or cls.type() not in Resource._reference:
                if cls.type() in Resource._reference and Resource._reference[cls.type()].isDefault and cls.isDefault:
                    raise ReferenceError(
                        f"Multiple resources of type {cls.type().name} register as default.")
                if cls.type() not in Resource._reference or not Resource._reference[cls.type()].isDefault:
                    Resource._reference[cls.type()] = cls

            if cls.type() in Resource._reference_variables and cls.isVariable:
                raise ReferenceError(
                    "Multiple resources of type {cls.type().name} register as variable.")

            if cls.isVariable:
                Resource._reference_variables[cls.type()] = cls

    def toTextJson(self, compileState: CompileState, formatter: ResourceTextFormatter) -> Union[Dict, List, str]:
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

    def store(self, compileState: CompileState) -> Resource:
        """
        Unlike storeToNbt, it does not matter how this resource is stored.
        Used if a resource that might be static should exist in the datapack.
        A NumberResource could decide to return a NumberResource or a NumberVariableResource.
        """
        raise TypeError(f"Resource {self} cannot be stored.")

    def storeToNbt(self, stack: NbtAddressResource, compileState: CompileState) -> Resource:
        """
        Called when this resource should be stored in a variable
        stores this variable to nbt.

        Args:
            stack: the stack on the data storage this resource should be stored to
            compileState: the Compile state
        """
        raise TypeError(f"{repr(self)} does not support this operation")

    def copy(self, target: ScoreboardValue, compileState: CompileState) -> Resource:
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

    def integer_value(self) -> int:
        """ Returns the associated integer value"""
        raise TypeError

    def string_value(self) -> str:
        """ Returns the associated string value"""
        raise TypeError

    def numericOperation(self, other: ValueResource, operator: BinaryOperator, compileState: CompileState) -> Resource:
        """
        Performes a numeric operation with this resource.
        The operation should be performed in-place
        """
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
            raise McScriptTypeError(
                f"{repr(self)} does not support the binary operation {operator.name}", compileState)
        raise ValueError("Unknown operator: " + repr(operator))

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

    def operation_test_relation(self, compileState: CompileState, relation: ScoreRelation,
                                other: Resource) -> ConditionalNode:
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

    def operation_call(self, compileState: CompileState, *parameters: Resource,
                       **keyword_parameters: Resource) -> Resource:
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

        # if the resource type is not already registered, import all resources
        if resourceType not in cls._reference:
            import_sub_modules()

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
    @abstractmethod
    def type() -> ResourceType:
        """ return the type of resource that is represented by this object"""
        return ResourceType.RESOURCE


VT = TypeVar("VT")


class ValueResource(Generic[VT], Resource):
    """
    Used for atomics in the build process
    """

    storage: ClassVar[MinecraftDataStorage] = MinecraftDataStorage.SCOREBOARD

    def __init__(self, static_value: Optional[VT], scoreboard_value: Optional[ScoreboardValue] = None):
        super().__init__()
        # the value that is known at compile time. May be None.
        self.static_value: Optional[VT] = static_value

        # The Scoreboard identifier which holds the value at runtime
        self.scoreboard_value: Optional[ScoreboardValue] = scoreboard_value

        if self.static_value is None and self.scoreboard_value is None:
            raise ValueError("Expected at least a static value or a scoreboard value, got none.")
    
    @property
    def is_static(self) -> bool:
        """ 
        A Resource is considered static if its value is only known at compile-time,
        but not (directly) at runtime
        """
        return self.scoreboard_value is None

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.VALUE_RESOURCE
    
    def toTextJson(self, compile_state: CompileState, formatter: ResourceTextFormatter):
        if self.static_value is not None:
            return format_text(str(self.static_value))
        return format_score(self.scoreboard_value.scoreboard.unique_name, self.scoreboard_value.value)

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.static_value == other.value

    def __hash__(self):
        return hash(self.static_value)
    
    def __repr__(self):
        return f"{type(self).__name__}({self.static_value}, {self.scoreboard_value})"


class ObjectResource(Resource, ABC):
    storage = MinecraftDataStorage.STORAGE

    def __init__(self, context: Context = None):
        super().__init__()
        # the empty context is a dummy
        from mcscript.compiler.Context import Context
        self.context = context or Context(0, None, ContextType.STRUCT, [])

    @staticmethod
    @abstractmethod
    def type() -> ResourceType:
        pass

    def getBasePath(self) -> NbtAddressResource:
        """ Returns the base path which contains the attributes of this object. """
        raise TypeError

    def getAttribute(self, compileState: CompileState, name: str) -> Resource:
        if name not in self.context:
            raise AttributeError(
                f"Property {name} does not exist for {type(self)}.")
        return self.context.find_resource(name)

    def setAttribute(self, compileState: CompileState, name: str, value: Resource) -> Resource:
        self.context.set_var(name, value)
        return value

    def __repr__(self):
        return f"Object {type(self).__name__}"
