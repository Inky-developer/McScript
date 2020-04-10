from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Optional

from Exceptions.compileExceptions import McScriptNameError
from mcscript.Exceptions.compileExceptions import McScriptArgumentsError
from mcscript.lang.resource.BooleanResource import BooleanResource
from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from mcscript.lang.resource.StructResource import StructResource
from mcscript.lang.resource.base.ResourceBase import ObjectResource, Resource, ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType
from mcscript.lang.utility import compareTypes

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


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
                                         f"Expected at most {len(variables)}", compileState)
        for var, value in zip(variables[:], parameters):
            key, varType = var
            value = compileState.load(value)
            if not compareTypes(value, varType.value):
                raise McScriptArgumentsError(
                    f"Struct object {struct.name} got identifier {key} with invalid type {value.type().name}, "
                    f"expected type {varType.value.type().name}",
                    compileState
                )
            if not isinstance(value, ValueResource):
                # raise NotImplementedError
                pass
            self.namespace[key] = value
            variables.remove(var)

        identifierKeys = [key for key, varType in variables]
        for key in keywordParameters:
            if key not in identifierKeys:
                raise McScriptArgumentsError(
                    f"Invalid keyword parameter {key} for struct initialization of {struct.name}. "
                    f"Expected one of: {', '.join(identifierKeys)}",
                    compileState
                )
            value = compileState.load(keywordParameters[key])
            if not isinstance(value, ValueResource):
                raise NotImplementedError
            # value.isStatic = False
            self.namespace[key] = value

        if variables:
            raise McScriptArgumentsError(
                f"Failed to initialize struct {struct.name}: Missing parameter(s) "
                f"{', '.join(str(key) for key, varType in variables)}",
                compileState
            )

    def storeToNbt(self, stack: NbtAddressResource, compileState: CompileState) -> Resource:
        self.nbtPath = stack
        for key in self.namespace:
            self.namespace[key] = self.namespace[key].storeToNbt(stack + NbtAddressResource(key), compileState)
        return self

    def setAttribute(self, compileState: CompileState, name: str, value: Resource) -> Resource:
        if not self.nbtPath:
            raise ReferenceError("Trying to set an attribute for an enum that has no nbtPath")
        if name not in self.namespace:
            raise McScriptNameError(f"Cannot set variable '{name}' for {self} which was never declared!", compileState)
        self.namespace[name] = value.storeToNbt(self.nbtPath + NbtAddressResource(name), compileState)
        return value

    def getAttribute(self, name: str) -> Resource:
        try:
            return self.namespace[name]
        except KeyError:
            try:
                return self.struct.getAttribute(name)
            except KeyError:
                raise AttributeError(f"Invalid attribute '{name}' of {repr(self)}")

    def getBasePath(self) -> NbtAddressResource:
        if not self.nbtPath:
            warnings.warn(f"Cannot get Nbt path of {self}: Unset")
            raise TypeError
        return self.nbtPath

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
