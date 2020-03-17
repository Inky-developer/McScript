from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from inspect import isabstract
from typing import List, TYPE_CHECKING, Any, Dict, Tuple, Optional, Union

from src.mcscript.data.Commands import Command
from src.mcscript.data.Config import Config
from src.mcscript.lang.Resource.AddressResource import AddressResource
from src.mcscript.lang.Resource.NullResource import NullResource
from src.mcscript.lang.Resource.ResourceBase import Resource, ValueResource
from src.mcscript.lang.Resource.ResourceType import ResourceType

if TYPE_CHECKING:
    from src.mcscript import Compiler, CompileState


@dataclass
class FunctionResult:
    code: Optional[str]
    # the returned resource
    resource: Resource
    inline: bool = True


class BuiltinFunction(ABC):
    """
    Base class for a builtin function. subclass to create a new builtin function.
    Can be called like a normal function but can generate code dynamically in python and accept an arbitrary
    amount of parameters.
    """
    functions: List[BuiltinFunction] = []

    def __init_subclass__(cls, hide=False):
        if not hide and not isabstract(cls):
            BuiltinFunction.functions.append(cls())

    def __init__(self):
        self.used = False

    def create(self, compileState: CompileState, *parameters: Resource) -> FunctionResult:
        result = self._makeResult(self.generate(compileState, *parameters), compileState.config)
        self._checkUsed(compileState)
        return result

    @classmethod
    def load(cls, compiler: Compiler):
        for function in cls.functions:
            compiler.loadFunction(function)

    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def returnType(self) -> ResourceType:
        pass

    @abstractmethod
    def generate(self, compileState: CompileState, *parameters: Resource) -> Union[str, FunctionResult]:
        """ throw a ArgumentError for invalid parameters."""
        pass

    def include(self, compileState: CompileState) -> Any:
        """
        Called when the function is used in the script
        if returns False, this function might be called again on the next use of this builtin
        """

    def _makeResult(self, result: Union[str, FunctionResult], config: Config) -> FunctionResult:
        """
        converts the result to a function result if it is a string
        :param result: the result
        :return: a function result dataclass
        """
        if isinstance(result, FunctionResult):
            return result

        if self.returnType() == ResourceType.NULL:
            resource = NullResource()
        else:
            # per default return the .ret scoreboard value
            resource = Resource.getResourceClass(self.returnType())(config.RETURN_SCORE, False)
        return FunctionResult(str(result), resource=resource)

    def _checkUsed(self, compileState):
        if not self.used:
            if self.include(compileState) is not False:
                self.used = True


class CachedFunction(BuiltinFunction, ABC):
    """ Like a normal function does not generate multiple times for the same parameters."""

    def __init__(self):
        super().__init__()
        self._cache: Dict[Tuple[Resource], Tuple[AddressResource, Resource]] = {}

    def create(self, compileState: CompileState, *parameters: Resource) -> FunctionResult:
        isStatic = all(isinstance(i, ValueResource) and i.hasStaticValue for i in parameters)
        if isStatic:
            if parameters not in self._cache:
                blockName = compileState.pushBlock()
                result = self._makeResult(self.generate(compileState, *parameters), compileState.config)
                compileState.writeline(result.code)
                self._checkUsed(compileState)
                compileState.popBlock()
                self._cache[parameters] = blockName, result.resource

            function, resource = self._cache[parameters]
            cmd = Command.RUN_FUNCTION(function=function)
            return FunctionResult(cmd, inline=True, resource=resource)
        # if any of the parameters is dynamic just use the normal behavior
        return super().create(compileState, *parameters)
