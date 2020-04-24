from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cached_property
from inspect import isabstract
from textwrap import dedent
from typing import Dict, List, Optional, Sequence, TYPE_CHECKING, Tuple, Union

from mcscript.Exceptions.compileExceptions import McScriptArgumentsError
from mcscript.data.commands import Command
from mcscript.lang.resource.AddressResource import AddressResource
from mcscript.lang.resource.FixedNumberResource import FixedNumberResource
from mcscript.lang.resource.NullResource import NullResource
from mcscript.lang.resource.NumberResource import NumberResource
from mcscript.lang.resource.SelectorResource import SelectorResource
from mcscript.lang.resource.StringResource import StringResource
from mcscript.lang.resource.TypeResource import TypeResource
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType
from mcscript.lang.resource.base.functionSignature import FunctionParameter, FunctionSignature

if TYPE_CHECKING:
    from mcscript import Compiler
    from mcscript.compiler.CompileState import CompileState


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

    _PATTERN_PARAMETER = re.compile(r"parameter *=> *((?:\[[\w=@.]+\] *)*) *([*+]?)(\w+): (\w+)+ *(.*)$")
    _PATTERN_MODIFIERS = re.compile(r"\[([\w=@.]+)\]")

    def __init_subclass__(cls, hide=False):
        if not hide and not isabstract(cls):
            BuiltinFunction.functions.append(cls())

    def __init__(self):
        self.used = False

    def type(self) -> ResourceType:
        return ResourceType.FUNCTION

    def create(self, compileState: CompileState, *parameters: Resource) -> FunctionResult:
        parameters = self.check_parameters(compileState, parameters)
        self._checkUsed(compileState)
        result = self._makeResult(self.generate(compileState, *parameters), compileState)
        # some functions need include afterwards (see setBlocks)
        self._checkUsed(compileState)
        return result

    def check_parameters(self, compileState: CompileState, parameters: Sequence[Resource]) -> List[Resource]:
        return self.getFunctionSignature.matchParameters(compileState, parameters)

    def requireRawParameters(self) -> bool:
        """
        Whether this builtin requires "raw" parameters. Raw parameters are not getting loaded and can be variables.
        (lvalues)
        """
        return False

    def ArgumentsError(self, arguments: List[Resource], msg: str, compileState: CompileState) -> McScriptArgumentsError:
        """ Creates a McScriptArgumentsError with some more error information"""
        return McScriptArgumentsError(self.getFunctionSignature.format_string.format(
            self.getFunctionSignature.arguments_format(arguments),
            msg
        ), compileState)

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

    @staticmethod
    def inline() -> bool:
        return True

    @cached_property
    def getFunctionSignature(self) -> FunctionSignature:
        """
        Parses the docstring and builds a function signature.
        """
        doc = dedent(self.__doc__.strip())
        parameters = []
        real_doc = []

        for line in doc.split("\n"):
            if match := self._PATTERN_PARAMETER.match(line.strip()):
                modifiers, *count, name, type_, parameter_doc = match.groups()
                is_optional = False
                mode = FunctionParameter.ResourceMode.STATIC | FunctionParameter.ResourceMode.NON_STATIC

                if not count[0]:
                    count = FunctionParameter.ParameterCount.ONCE
                else:
                    count = FunctionParameter.ParameterCount.ONE_OR_MORE if count[0] == "+" else \
                        FunctionParameter.ParameterCount.ARBITRARY
                default = None

                for mod_match in self._PATTERN_MODIFIERS.findall(modifiers):
                    if mod_match.lower().startswith("optional"):
                        raw: str = mod_match.split("=")[1]
                        if raw.isdecimal():
                            default = NumberResource(int(raw), True)
                        elif all(i in "0123456789." for i in raw):
                            default = FixedNumberResource.fromNumber(float(raw))
                        elif raw.lower() == "null":
                            default = NullResource()
                        elif raw.startswith("@"):
                            default = SelectorResource(raw, True)
                        else:
                            default = StringResource(raw, True)
                    elif mod_match.lower() == "static":
                        mode = FunctionParameter.ResourceMode.STATIC
                    elif mod_match.lower() == "non_static":
                        mode = FunctionParameter.ResourceMode.NON_STATIC

                if type_ == "Resource":
                    resourceType = Resource
                elif type == "ValueResource":
                    resourceType = ValueResource
                else:
                    resourceType = Resource.getResourceClass(ResourceType(type_))
                parameters.append(FunctionParameter(
                    name,
                    TypeResource(resourceType),
                    count=count,
                    defaultValue=default,
                    accepts=mode,
                    documentation=parameter_doc
                ))
            else:
                real_doc.append(line)

        return FunctionSignature(
            self,
            parameters,
            self.returnType(),
            inline=self.inline(),
            documentation="\n".join(real_doc)
        )

    @abstractmethod
    def generate(self, compileState: CompileState, *parameters: Resource) -> Union[str, FunctionResult]:
        """ throw a ArgumentError for invalid parameters."""
        pass

    def include(self, compileState: CompileState) -> bool:
        """
        Called when the function is used in the script
        if returns False, this function might be called again on the next use of this builtin
        """

    def _makeResult(self, result: Union[str, FunctionResult], compileState: CompileState) -> FunctionResult:
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
            resourceCls = Resource.getResourceClass(self.returnType())
            if not issubclass(resourceCls, ValueResource):
                raise TypeError(f"Function {self} returned invalid resource type '{resourceCls.__name__}'")
            resource = resourceCls(compileState.config.RETURN_SCORE, False)
        return FunctionResult(str(result), resource=resource)

    def _checkUsed(self, compileState):
        if not self.used:
            if self.include(compileState) is not False:
                self.used = True


class CachedFunction(BuiltinFunction, ABC):
    """ Like a normal function does not generate multiple times for the same parameters."""

    def __init__(self):
        super().__init__()
        self._cache: Dict[Tuple[Resource], AddressResource] = {}

    def create(self, compileState: CompileState, *parameters: Resource) -> FunctionResult:
        parameters = tuple(self.check_parameters(compileState, parameters))
        isStatic = all(isinstance(i, ValueResource) and i.hasStaticValue for i in parameters)
        if isStatic:
            if parameters not in self._cache:
                blockName = compileState.pushBlock()
                self._checkUsed(compileState)
                result = self.generate(compileState, *parameters)
                compileState.writeline(result)
                compileState.popBlock()
                self._cache[parameters] = blockName

            function = self._cache[parameters]
            stack = compileState.expressionStack.next()
            cmd = Command.RUN_FUNCTION(function=function)
            if self.returnType() != NullResource:
                cmd += "\n" + Command.SET_VALUE_EQUAL(stack=stack, stack2=compileState.config.RETURN_SCORE)
                resourceCls = Resource.getResourceClass(self.returnType())
                if not issubclass(resourceCls, ValueResource):
                    raise TypeError(f"Function {self} returned invalid resource type '{resourceCls.__name__}'")
                resource = resourceCls(stack, False)
            else:
                resource = NullResource()

            return FunctionResult(cmd, inline=True, resource=resource)
        # if any of the parameters is dynamic just use the normal behavior
        return super().create(compileState, *parameters)

    @staticmethod
    def inline() -> bool:
        return False

    @abstractmethod
    def generate(self, compileState: CompileState, *parameters: Resource) -> str:
        pass
