from typing import Union

from mcscript.compiler.CompileState import CompileState
from mcscript.lang.builtins.builtins import BuiltinFunction, FunctionResult
from mcscript.lang.resource.TupleResource import TupleResource
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.resource.base.ResourceType import ResourceType


class ArrayOf(BuiltinFunction):
    """
    parameter => *elements: Resource the elements for this array
    """

    def name(self) -> str:
        return "arrayOf"

    def returnType(self) -> ResourceType:
        return ResourceType.TUPLE

    def requireRawParameters(self) -> bool:
        return True

    def generate(self, compileState: CompileState, *parameters: Resource) -> Union[str, FunctionResult]:
        return FunctionResult(None, TupleResource(*parameters))
