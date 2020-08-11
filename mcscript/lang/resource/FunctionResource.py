from __future__ import annotations

from typing import Tuple, Dict, List, TYPE_CHECKING

from lark import Tree

from mcscript.compiler.ContextType import ContextType
from mcscript.ir.components import FunctionCallNode
from mcscript.lang.Type import Type
from mcscript.lang.atomic_types import Function
from mcscript.lang.resource.NullResource import NullResource
from mcscript.lang.resource.base.ResourceBase import GenericFunctionResource, Resource

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState
    from mcscript.lang.resource.base.functionSignature import FunctionSignature


class FunctionResource(GenericFunctionResource):
    """
    A function which will execute at runtime
    """

    def __init__(self, name: str, function_signature: FunctionSignature, code: Tree):
        self.function_signature = function_signature
        self.code = code
        self.name = name

    def handle_parameters(self, compile_state: CompileState, parameters: List[Resource]) -> List[Resource]:
        return self.function_signature.matchParameters(compile_state, parameters)

    def call(self, compile_state: CompileState, parameters: Tuple[Resource],
             keyword_parameters: Dict[str, Resource]) -> Resource:
        with compile_state.node_block(ContextType.FUNCTION, self.code.line, self.code.column) as function_name:
            for template, parameter in zip(self.function_signature.parameters, parameters):
                compile_state.currentContext().add_var(template.name, parameter)
            compile_state.compileFunction(self.code)
            return_value = compile_state.currentContext().return_resource or NullResource()

        compile_state.ir.append(FunctionCallNode(compile_state.ir.find_function_node(function_name)))
        return return_value

    def type(self) -> Type:
        return Function
