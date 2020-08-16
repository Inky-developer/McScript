from __future__ import annotations

from abc import ABC, abstractmethod
from typing import (TYPE_CHECKING, Dict, List, Optional, Type,
                    Union, TypeVar, Generic)

from mcscript.exceptions.exceptions import McScriptUnsupportedOperationError
from mcscript.ir.command_components import BinaryOperator
from mcscript.ir.components import ConditionalNode, StoreFastVarNode
from mcscript.lang.Type import Type
from mcscript.lang.atomic_types import Iterator
from mcscript.utils.JsonTextFormat.objectFormatter import format_score, format_text
from mcscript.utils.resources import ScoreboardValue

if TYPE_CHECKING:
    from mcscript.ir.command_components import ScoreRelation
    from mcscript.utils.JsonTextFormat.ResourceTextFormatter import ResourceTextFormatter
    from mcscript.compiler.CompileState import CompileState


class Resource(ABC):
    def to_json_text(self, compileState: CompileState, formatter: ResourceTextFormatter) -> Union[Dict, List, str]:
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

    def get_iterator(self, compileState: CompileState) -> IteratorResource:
        """
        If this resource supports iterations, this method is called to get an iterator.

        Args:
            compileState: the compile state

        Returns:
            An Iterator

        Raises:
            TypeError: if this operation is not supported
        """
        raise TypeError()

    def integer_value(self) -> int:
        """ Returns the associated integer value"""
        raise TypeError()

    def string_value(self) -> str:
        """ Returns the associated string value"""
        raise TypeError()

    def numericOperation(self, other: ValueResource, operator: BinaryOperator, compileState: CompileState) -> Resource:
        """
        Performs a numeric operation with this resource.
        The operation should be performed in-place
        """
        if not isinstance(other, type(self)):
            raise TypeError()
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
            raise McScriptUnsupportedOperationError(operator.name, self.type(), other.type(), compileState)
        raise ValueError("Unknown operator: " + repr(operator))

    def operation_plus(self, other: ValueResource, compileState: CompileState) -> ValueResource:
        raise TypeError()

    def operation_minus(self, other: ValueResource, compileState: CompileState) -> ValueResource:
        raise TypeError()

    def operation_times(self, other: ValueResource, compileState: CompileState) -> ValueResource:
        raise TypeError()

    def operation_divide(self, other: ValueResource, compileState: CompileState) -> ValueResource:
        raise TypeError()

    def operation_modulo(self, other: ValueResource, compileState: CompileState) -> ValueResource:
        raise TypeError()

    def operation_negate(self, compileState: CompileState) -> Resource:
        """
        Returns a resource whose value negated is the value of this resource

        Args:
            compileState: the compileState

        Returns:
            the new resource
        """
        raise TypeError()

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
        raise TypeError()

    def operation_call(self, compileState: CompileState, *parameters: Resource,
                       **keyword_parameters: Resource) -> Resource:
        """
        If this method is implemented, the resource can be treated like a function

        Args:
            compileState: the compile state
            parameters: a list of parameters
            keyword_parameters: a list of keyword parameters, currently they are not yet supported

        Returns:
            a new resource
        """
        raise TypeError()

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

    @abstractmethod
    def supports_scoreboard(self) -> bool:
        """
        Returns:
            Whether this resource can live on a scoreboard
        """
        ...

    @abstractmethod
    def supports_storage(self) -> bool:
        """
        Returns:
            Whether this resource can live on a data storage
        """

    def supports_non_static(self):
        """
        Returns:
            Whether there is any way this resource can be used dynamically
        """
        return self.supports_scoreboard() or self.supports_non_static()

    @abstractmethod
    def type(self) -> Type:
        """ return the type of resource that is represented by this object"""
        ...


VT = TypeVar("VT")


class ValueResource(Generic[VT], Resource, ABC):
    """
    Used for atomics in the build process
    """

    def __init__(self, static_value: Optional[VT], scoreboard_value: Optional[ScoreboardValue] = None):
        super().__init__()
        # the value that is known at compile time. May be None.
        self.static_value: Optional[VT] = static_value

        # The Scoreboard identifier which holds the value at runtime
        self.scoreboard_value: Optional[ScoreboardValue] = scoreboard_value

        if self.static_value is None and self.scoreboard_value is None:
            raise ValueError("Expected at least a static value or a scoreboard value, got none.")

    def copy(self, target: ScoreboardValue, compileState: CompileState) -> ValueResource:
        """
        Copy this resource.
        Note the this will be called with target == self.scoreboard_value, in this case a copy is not needed

        Args:
            target: the target value
            compileState: the compile state

        Returns:
            A new copied resource
        """
        if self.is_static:
            return self.store(compileState, target)

        if target == self.scoreboard_value:
            return self

        compileState.ir.append(StoreFastVarNode(target, self.scoreboard_value))
        return type(self)(self.static_value, target)

    @property
    def is_static(self) -> bool:
        """ 
        A Resource is considered static if its value is only known at compile-time,
        but not (directly) at runtime
        """
        return self.scoreboard_value is None

    def store(self, compileState: CompileState, scoreboard_address: ScoreboardValue = None,
              keep_static_value: bool = False) -> ValueResource:
        if not self.is_static:
            return type(self)(self.static_value, self.scoreboard_value)

        scoreboard_address = scoreboard_address or compileState.expressionStack.next()
        compileState.ir.append(StoreFastVarNode(scoreboard_address, self.static_value))

        return type(self)(self.static_value if keep_static_value else None, scoreboard_address)

    def to_json_text(self, compile_state: CompileState, formatter: ResourceTextFormatter):
        if self.static_value is not None:
            return format_text(str(int(self.static_value)))
        return format_score(self.scoreboard_value)

    def supports_scoreboard(self) -> bool:
        return True

    def supports_storage(self) -> bool:
        return False

    def __repr__(self):
        return f"{type(self).__name__}({self.static_value}, {self.scoreboard_value})"


class GenericFunctionResource(Resource, ABC):
    """
    A generic function.

    Mcscript has two types of functions:
        - "normal" functions, defined via the `fun` keyword.
          Can take a fixed number of variables and execute at runtime
        - macro functions, defined via the `macro` keyword or in the stdlib.
          Generate code a compile time

    A basic function only needs a function to tell whether it accepts some parameters and, if it does,
    a function that generates ir code.
    """

    @abstractmethod
    def handle_parameters(self, compile_state: CompileState, parameters: List[Resource]) -> List[Resource]:
        """
        Handles the parameters. Raises if the parameters are invalid.

        Args:
            compile_state: The compile state
            parameters: A list of resources

        Returns:
            the handled resources
        """

    @abstractmethod
    def call(self, compile_state: CompileState, parameters: List[Resource],
             keyword_parameters: Dict[str, Resource]) -> Resource:
        """
        Generates the ir code and returns a resource.

        Args:
            compile_state: the compile state
            parameters: the function parameters
            keyword_parameters: named function parameters

        Returns:
            A resource as result
        """

    def operation_call(self, compile_state: CompileState, *parameters: Resource,
                       **keyword_parameters: Resource) -> Resource:
        parameters = self.handle_parameters(compile_state, list(parameters))
        return self.call(compile_state, parameters, keyword_parameters)

    def supports_scoreboard(self) -> bool:
        return False

    def supports_storage(self) -> bool:
        return False


class ObjectResource(Resource, ABC):
    """
    A generic object.
    Each object has an internal namespace, which should be possible to access
    """

    def __init__(self, public_namespace: Dict[str, Resource] = None):
        self.public_namespace = public_namespace or {}

    @property
    def is_static(self) -> bool:
        """ returns whether *ALL* public members are static"""
        return all(i.is_static for i in self.public_namespace.values() if isinstance(i, ValueResource))

    @property
    def is_any_static(self) -> bool:
        """ returns whether *ANY* public member is static. If True `store` can be called"""
        return any(i.is_static for i in self.public_namespace.values() if isinstance(i, ValueResource))

    def getAttribute(self, compileState: CompileState, name: str) -> Resource:
        return self.public_namespace[name]

    def store(self, compileState: CompileState) -> Resource:
        # store all of the public namespace
        self.public_namespace = {name: value.store(compileState) for name, value in self.public_namespace.items()}
        return self


class IteratorResource(Resource, ABC):
    @abstractmethod
    def next(self) -> Optional[Resource]:
        """
        Calculate and return the next element.
        If the iterator is empty, return None

        Returns:
            Either the next element or None
        """
        ...

    def type(self) -> Type:
        return Iterator

    def supports_scoreboard(self) -> bool:
        return False

    def supports_storage(self) -> bool:
        return False
