from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from src.mcscript.Exceptions import McScriptArgumentsError, McScriptAttributeError
from src.mcscript.lang.resource.BooleanResource import BooleanResource
from src.mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from src.mcscript.lang.resource.StructResource import StructResource
from src.mcscript.lang.resource.base.ResourceBase import ObjectResource, Resource, ValueResource
from src.mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from src.mcscript import CompileState


class StructObjectResource(ObjectResource):
    """
    The object representation of a struct.
    """

    def __init__(self, struct: StructResource, compileState: CompileState, *parameters: Resource, **keywordParameters):
        super().__init__()
        # the nbtPath specifies where in the data storage this enum is located. it gets set when storeToNbt is called.
        self.nbtPath: Optional[NbtAddressResource] = None
        self.struct = struct
        self.build_namespace(struct, compileState, *parameters, **keywordParameters)

    def build_namespace(self, struct: StructResource, compileState: CompileState, *parameters: Resource,
                        **keywordParameters: Resource):
        variables = struct.getDeclaredVariables()
        if len(parameters) > len(variables):
            raise McScriptArgumentsError(f"Invalid number of parameters for struct initialization of {struct.name}. "
                                         f"Expected at most {len(variables)}")
        for var, value in zip(variables[:], parameters):
            key, varType = var
            value = compileState.load(value)
            if not isinstance(value, varType.value):
                raise McScriptArgumentsError(
                    f"Struct object {struct.name} got identifier {key} with invalid type {value.type().name}, "
                    f"expected type {varType.value.type().name}"
                )
            if not isinstance(value, ValueResource):
                raise NotImplementedError
            self.namespace[key] = value
            variables.remove(var)

        identifierKeys = [key for key, varType in variables]
        for key in keywordParameters:
            if key not in identifierKeys:
                raise McScriptArgumentsError(
                    f"Invalid keyword parameter {key} for struct initialization of {struct.name}. "
                    f"Expected one of: {', '.join(identifierKeys)}"
                )
            value = compileState.load(keywordParameters[key])
            if not isinstance(value, ValueResource):
                raise NotImplementedError
            # value.isStatic = False
            self.namespace[key] = value

        if variables:
            raise McScriptArgumentsError(
                f"Failed to initialize struct {struct.name}: Missing parameter(s) "
                f"{', '.join(str(key) for key, varType in variables)}"
            )

    def storeToNbt(self, stack: NbtAddressResource, compileState: CompileState) -> Resource:
        self.nbtPath = stack
        for key in self.namespace:
            self.namespace[key] = self.namespace[key].storeToNbt(stack + NbtAddressResource(key), compileState)
        return self

    def setAttribute(self, compileState: CompileState, name: str, value: Resource) -> Resource:
        if not self.nbtPath:
            raise ReferenceError("Trying to set an attribute for an enum that has no nbtPath")
        self.namespace[name] = value.storeToNbt(self.nbtPath + NbtAddressResource(name), compileState)
        return value

    def getAttribute(self, name: str) -> Resource:
        try:
            return self.namespace[name]
        except KeyError:
            try:
                return self.struct.getAttribute(name)
            except KeyError:
                raise McScriptAttributeError(f"Invalid attribute {name} of {repr(self)}")

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.STRUCT_OBJECT

    def convertToBoolean(self, compileState: CompileState) -> BooleanResource:
        return BooleanResource.TRUE

    def toNumber(self) -> int:
        raise TypeError

    def toString(self) -> str:
        raise TypeError

    def __repr__(self):
        return f"StructObjectResource '{self.struct.name}'"
