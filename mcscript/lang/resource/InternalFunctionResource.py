from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING, Tuple

from mcscript.lang.resource.TypeResource import TypeResource
from mcscript.lang.resource.base.FunctionResource import FunctionResource
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.utility import compareTypes

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState

# used to generate unique function names
name_counter: int = 0


class InternalFunctionResource(FunctionResource, ABC):
    """
    Function class used for internal functions like `list.length`.
    Implemented in python and does not use a context stack.
    """

    def __init__(self, parameters: List[Tuple[str, TypeResource]], return_type: TypeResource):
        global name_counter

        name = f"internal_function_{name_counter}"
        name_counter += 1

        super().__init__(name, parameters, return_type, None)

    @staticmethod
    def inline() -> bool:
        return True

    def operation_call(self, compileState: CompileState, *parameters: Resource,
                       **keywordParameters: Resource) -> Resource:
        parameters = self.signature.matchParameters(compileState, parameters)

        parameter_dict = {}
        for parameter_data, parameter in zip(self.parameters, parameters):
            parameter_name, _ = parameter_data
            parameter_dict[parameter_name] = parameter

        return_value = self.execute(compileState, **parameter_dict)

        if not compareTypes(return_value, self.returnType.value):
            raise TypeError(f"Bad return value {return_value} for internal function. Expected type {self.returnType}")

        return return_value

    @abstractmethod
    def execute(self, compileState: CompileState, **parameters: Resource) -> Resource:
        """
        Executes the function and returns a resource that should be returned from this function

        Args:
            compileState: the compile state
            **parameters: named parameters, as specified in __init__ super call

        Returns:
            A resource that should be returned from this function
        """
