from __future__ import annotations

from abc import ABC, abstractmethod
from functools import cached_property
from typing import TypeVar, Generic

from mcscript.data.Config import Config
from mcscript.ir.components import *

if TYPE_CHECKING:
    from mcscript.ir.IrMaster import IrMaster

T = TypeVar("T")


class IRBackend(Generic[T], ABC):
    """ 
    A backend for the intermediate representation used by mcscript.

    Each class implementing IRBackend can convert the ir-nodes to 
    some kind of code.
    For example, the `McDatapackBackend` converts to mcfunctions.
    """

    def __init__(self, config: Config):
        self.config = config

    def generate(self, ir_master: IrMaster) -> T:
        for function_node in ir_master.function_nodes:
            self.handle_function_node(function_node)

        self.on_finish()

        return self._get_value()

    def handle(self, node: IRNode):
        """
        Handles a node
        """
        handler = f"handle_{node.node_id}"
        handler_fn = getattr(self, handler, None)

        if handler_fn is None or not callable(handler_fn):
            raise AttributeError(
                f"Backend cannot handle node of type {node.node_id}")

        handler_fn(node)

    def handle_children(self, node: IRNode):
        """
        Handles each child of this node
        """
        for child in node.inner_nodes:
            self.handle(child)

    def on_finish(self):
        """ Called when the generation is finished. Used to clean up."""
        pass

    # noinspection PyNestedDecorators,PyPropertyDefinition
    @cached_property
    @classmethod
    def identifier(cls) -> str:
        return cls._identifier()

    @abstractmethod
    def _get_value(self) -> T:
        ...

    @classmethod
    @abstractmethod
    def _identifier(cls) -> str:
        """
        Returns the identifier for this backend
        Used to select this backend from a list of all backends
        """
        ...

    @abstractmethod
    def handle_function_node(self, node: FunctionNode):
        ...

    @abstractmethod
    def handle_function_call_node(self, node: FunctionCallNode):
        ...

    @abstractmethod
    def handle_execute_node(self, node: ExecuteNode):
        ...

    @abstractmethod
    def handle_conditional_node(self, node: ConditionalNode):
        ...

    @abstractmethod
    def handle_if_node(self, node: IfNode):
        ...

    @abstractmethod
    def handle_store_fast_var_node(self, node: StoreFastVarNode):
        ...

    @abstractmethod
    def handle_store_fast_var_from_result_node(self, node: StoreFastVarFromResultNode):
        ...

    @abstractmethod
    def handle_store_var_node(self, node: StoreVarNode):
        ...

    @abstractmethod
    def handle_store_var_from_result_node(self, node: StoreVarFromResultNode):
        ...

    @abstractmethod
    def handle_fast_var_operation_node(self, node: FastVarOperationNode):
        ...

    @abstractmethod
    def handle_invert_node(self, node: InvertNode):
        ...

    @abstractmethod
    def handle_message_node(self, node: MessageNode):
        ...

    @abstractmethod
    def handle_command_node(self, node: CommandNode):
        ...

    @abstractmethod
    def handle_set_block_node(self, node: SetBlockNode):
        ...

    @abstractmethod
    def handle_summon_node(self, node: SummonNode):
        ...

    @abstractmethod
    def handle_kill_node(self, node: KillNode):
        ...

    @abstractmethod
    def handle_scoreboard_init_node(self, node: ScoreboardInitNode):
        ...
