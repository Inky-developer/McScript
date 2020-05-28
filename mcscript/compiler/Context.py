from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from mcscript.analyzer.VariableContext import VariableContext
from mcscript.compiler.ContextType import ContextType
from mcscript.lang.resource.base.ResourceBase import Resource


class Context:
    """
    Manages a single context. A context is unique to each block that is entered, which includes ia. functions.

    A `Context` keeps track of:
        * the previous `Context`
        * The numerical id of this `Context`
        * the variables unique to this context
        * the type of context, ia. if it can be evaluated at compile time (not influenced by inner non-static contexts)
    """

    @dataclass()
    class Variable:
        """
        The value class of the namespace of the context
        """
        resource: Resource = field()
        context: Optional[VariableContext] = field(default=None)

    def __init__(
            self,
            index: int,
            ctx_type: ContextType,
            variable_context: List[VariableContext],
            predecessor: Context = None
    ):
        self.index = index
        self.context_type = ctx_type
        self.predecessor = predecessor

        # make a simple lookup table name -> ctx
        self.variable_context = {i.identifier: i for i in variable_context}

        # the namespace of variables unique to this context
        self.namespace: Dict[str, Context.Variable] = {}

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

    def add_var(self, name: str, value: Resource):
        """
        Adds a variable to this context and assigns it the correct variable context.
        Note that there must be a valid variable context!
        Fails if the variable does already exist.

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

        variable_context = self.variable_context[name]
        self.namespace[name] = self.Variable(value, variable_context)

    def set_var(self, name: str, value: Resource):
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
            raise KeyError(f"Variable '{name}' does not exist!")
