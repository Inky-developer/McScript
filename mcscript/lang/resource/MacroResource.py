from typing import Tuple, Dict, List, Callable

from mcscript.compiler.CompileState import CompileState
from mcscript.lang.resource.base.ResourceBase import GenericFunctionResource, Resource
from mcscript.lang.resource.base.ResourceType import ResourceType
from mcscript.lang.resource.base.functionSignature import FunctionSignature


class MacroResource(GenericFunctionResource):
    """
    A macro is a function that is executed at compile time and creates code.
    Macros in mcscript are any python code, which have access to the almighty `CompileState` object.
    Optionally a macro can return a resource, if it does not, Null is returned.
    Macros are very powerful, as they can do many things that are not possible within minecraft, like io or expensive
    computations.
    """

    def __init__(self, signature: FunctionSignature, name: str, function: Callable[..., Resource]):
        self.signature = signature
        self.name = name
        self.macro = function

    def handle_parameters(self, compile_state: CompileState, parameters: Tuple[Resource]) -> List[Resource]:
        return self.signature.matchParameters(compile_state, parameters)

    def call(self, compile_state: CompileState, parameters: List[Resource],
             keyword_parameters: Dict[str, Resource]) -> Resource:
        assert not keyword_parameters
        return self.macro(compile_state, *parameters)

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.MACRO

    def __repr__(self):
        return f"macro {self.signature.signature_string()}"
