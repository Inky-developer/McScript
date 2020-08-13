from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from mcscript import Logger
from mcscript.analyzer.VariableContext import VariableContext
from mcscript.compiler.ContextType import ContextType
from mcscript.lang.resource.NullResource import NullResource
from mcscript.lang.resource.StructObjectResource import StructObjectResource
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.utils.Scoreboard import Scoreboard
from mcscript.utils.addressCounter import ScoreboardAddressCounter, StorageAddressCounter
from mcscript.utils.resources import DataPath

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class Context:
    """
    Manages a single context. A context is unique to each block that is entered, which includes ia. functions.

    A `Context` keeps track of:
        * The previous `Context`
        * The definition of this context as (line, column)
        * The numerical id of this `Context` (deprecated, unused)
        * The variables unique to this context
        * The type of context, ia. if it can be evaluated at compile time (not influenced by inner non-static contexts)
        * A template string for context specific variable names
        * A template string for nbt variable names
        * An optional resource which is the resource that is returned from this stack.
    """

    @dataclass()
    class Variable:
        """
        The value class of the namespace of the context
        """
        resource: Resource = field()
        context: Optional[VariableContext] = field(default=None, repr=False)

    def __init__(
            self,
            index: int,
            definition: Optional[Tuple[int, int]],
            ctx_type: ContextType,
            variable_context: List[VariableContext],
            main_scoreboard: Scoreboard,
            base_path: DataPath,
            predecessor: Context = None,
    ):
        self.index = index
        self.definition = definition
        self.context_type = ctx_type
        self.predecessor = predecessor

        # make a simple lookup table name -> ctx
        self.variable_context: Dict[str, VariableContext] = {i.identifier: i for i in variable_context}

        # the namespace of variables unique to this context
        self.namespace: Dict[str, Context.Variable] = {}

        # formats scoreboard variables to ".exp<x>_<varId>"
        self.scoreboard_formatter = ScoreboardAddressCounter(main_scoreboard, f".exp{self.index}_{{}}")
        # for nbt names
        self.nbt_format = StorageAddressCounter(base_path, f"{self.index}_{{}}" if self.index != 0 else "{}")

        # A resource which is returned when this context is popped
        self.return_resource: Optional[Resource] = None

    def clear(self):
        """
        resets this context by clearing the namespace

        Returns:
            None
        """
        self.namespace.clear()
        self.return_resource = None

    def find_var(self, name: str) -> Optional[Context.Variable]:
        """
        Recursively looks for a variable with key `name`.

        Args:
            name: The name of the variable

        Returns:
            The variable or None if not found
        """
        if name in self.namespace:
            return self.namespace[name]

        if self.predecessor is not None:
            return self.predecessor.find_var(name)

        return None

    def find_resource(self, name: str) -> Optional[Resource]:
        """
        Like `find_var` but returns just the resource.

        Args:
            name: The name of the variable

        Returns:
            The resource or None if not found
        """
        return None if (var := self.find_var(name)) is None else var.resource

    def find_resource_name(self, resource: Resource) -> Optional[str]:
        """
        Searches for a stored Resource that is `resource` and, if found, returns its name-

        Args:
            resource: The resource of which the name is searched

        Returns:
            The name of the resource if found
        """
        for name, variable in self.namespace.items():
            if variable.resource is resource:
                return name

        if self.predecessor is None:
            return None

        return self.predecessor.find_resource_name(resource)

    def add_var(self, name: str, value: Resource) -> Resource:
        """
        Adds a variable to this context and assigns it the correct variable context.
        Note that there must be a valid variable context!
        Fails if the variable name does already exist.

        Args:
            name: the name of the variable
            value: the resource

        Returns:
            None

        Raises:
            ValueError: If the resource does already exist
        """
        if name in self.namespace:
            raise ValueError(f"Variable {name} does already exist!")

        # should an error be thrown when no history is found?
        variable_context = self.variable_context.get(name, None)
        if variable_context is None:
            Logger.debug(f"[Context] No context data available for variable '{name}' ({value})")

        self.namespace[name] = self.Variable(value, variable_context)
        return value

    def set_var(self, name: str, value: Resource) -> Resource:
        """
        Overwrites the value of an existing resource.
        If the variable is not in this namespace, the next lower namespace will be used.
        Raises if the resource does not exist in this or any lower namespace.

        Args:
            name: The name of the variable
            value: The resource

        Returns:
            None

        Raises:
            KeyError: If the variable does not exist
        """

        if name in self.namespace:
            self.namespace[name].resource = value
        elif self.predecessor is not None:
            self.predecessor.set_var(name, value)
        else:
            raise KeyError(f"Variable '{name}' does not exist and thus cannot be changed!")

        return value

    def as_dict(self) -> Dict[str, Context.Variable]:
        """
        Creates a dictionary containing all variable names from this and earlier contexts.
        If a variable shares the same name on multiple contexts, the variable in the highest context will be kept.

        Returns:
            A Dict containing all variables from this and previous contexts
        """
        if self.predecessor is not None:
            data = self.predecessor.as_dict()
        else:
            data = {}

        data.update(self.namespace)
        return data

    def update_static_resources(self, compile_state: CompileState):
        """
        Goes through every resource of the previous context and checks if it is still allowed to be static.
        A static resource will not be allowed to continue being static if:
            - self is not a static context AND
            - the variable is written to in this context

        If a resource is not allowed to be static, it will be stored

        Returns:
            None
        """
        if self.predecessor is None:
            raise ValueError()

        if self.context_type.hasStaticContext:
            return

        for name, variable in self.predecessor.namespace.items():
            resource, var_context = variable.resource, variable.context
            if var_context is None:
                if isinstance(resource, (ValueResource, StructObjectResource)):
                    raise ValueError(f"[INTERNAL COMPILER ERROR] The context of {name} does not exist.")
                continue
            for write in var_context.writes:
                if write.master_context == self.definition:
                    # the resource should be stored
                    self.predecessor.set_var(name, resource.store(compile_state))

    def get_return_resource_or_null(self) -> Resource:
        """
        Returns:
            `self.return_resource` if it is not None, else a `NullResource`
        """
        return self.return_resource or NullResource()

    def __contains__(self, item) -> bool:
        """
        Tests recursively if the item is in this contexts namespace or below
        """
        if item in self.namespace:
            return True

        if self.predecessor:
            return item in self.predecessor

        return False

    def __str__(self):
        return f"Context(index={self.index},type={self.context_type},namespace={self.namespace})"
