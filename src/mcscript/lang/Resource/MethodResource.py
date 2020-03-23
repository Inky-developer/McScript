from src.mcscript import CompileState
from src.mcscript.compiler import Namespace
from src.mcscript.lang.Resource.BooleanResource import BooleanResource
from src.mcscript.lang.Resource.FunctionResource import Function
from src.mcscript.lang.Resource.ResourceBase import ObjectResource
from src.mcscript.lang.Resource.ResourceType import ResourceType


class MethodResource(ObjectResource):
    """
    A bound function
    """

    def __init__(self, function: Function):
        super().__init__()
        self.function = function

    def setNamespace(self, namespace: Namespace):
        pass

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.METHOD

    def convertToBoolean(self, compileState: CompileState) -> BooleanResource:
        return BooleanResource.TRUE

    def toNumber(self) -> int:
        raise TypeError

    def toString(self) -> str:
        raise TypeError
