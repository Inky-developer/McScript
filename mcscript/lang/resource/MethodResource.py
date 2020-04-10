from mcscript.compiler.CompileState import CompileState
from mcscript.compiler.Namespace import Namespace
from mcscript.lang.resource.BooleanResource import BooleanResource
from mcscript.lang.resource.base.FunctionResource import FunctionResource
from mcscript.lang.resource.base.ResourceBase import ObjectResource
from mcscript.lang.resource.base.ResourceType import ResourceType


class MethodResource(ObjectResource):
    """
    A bound function
    """

    def __init__(self, function: FunctionResource):
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
