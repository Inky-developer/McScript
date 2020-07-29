from __future__ import annotations
from typing import Dict
from mcscript.data.Config import Config
from mcscript.ir.IRBackend import IRBackend
from mcscript.ir.components import *
from mcscript.ir.backends.mc_datapack_backend.Datapack import Datapack
from mcscript.ir.backends.mc_datapack_backend.utils import position_to_str


class McDatapackBackend(IRBackend[Datapack]):
    def __init__(self, config: Config):
        super().__init__(config)

        self.datapack = Datapack(self.config)
        self.files = self.datapack.getMainDirectory().getPath("functions").files

        # A list of all constants used by this backend
        self.constant_scores: Dict[int, ScoreboardValue] = {}

    def _get_constant(self, value: int, scoreboard: Scoreboard) -> ScoreboardValue:
        if value in self.constant_scores:
            return self.constant_scores[value]

        scoreboard_value = ScoreboardValue(
            Identifier(f".const_{value}"),
            scoreboard
        )

        self.constant_scores[value] = scoreboard_value
        return scoreboard_value

    def write_line(self, text: str):
        self.files.get().write(f"{text}\n")

    @classmethod
    def _identifier(cls):
        return "mc_datapack"

    def _get_value(self) -> Datapack:
        return self.datapack

    def on_finish(self):
        # Add constant values
        nodes = [StoreFastVarNode(self.constant_scores[i], i)
                 for i in self.constant_scores]
        function = FunctionNode("init_constants", nodes)
        self.handle(function)

    def handle_function_node(self, node: FunctionNode):
        self.files.push(f"{node['name']}.mcfunction")
        self.handle_children(node)

    def handle_function_call_node(self, node: FunctionCallNode):
        value = node["name"]
        self.write_line(
            f"function {value.base}:{value.path}"
        )

    def handle_execute_node(self, node: ExecuteNode):
        SUB_NODE_TO_STRING = {
            ExecuteNode.As: lambda node: f"as {node['selector']}",
            ExecuteNode.At: lambda node: f"at {node['selector']}",
            ExecuteNode.Positioned: lambda node: f"positioned {position_to_str(node['pos'])}",
            ExecuteNode.Anchored: lambda node: f"anchored {node['anchor'].value}"
        }

        sub_nodes = [SUB_NODE_TO_STRING[type(i)](
            i) for i in node["components"]]
        if not sub_nodes:
            raise ValueError("Empty execute node")
        execute_base = f"execute {' '.join(sub_nodes)} run "

        # ToDO: when optimizing, create a new file for multiple inner nodes
        for command in node.inner_nodes:
            self.files.get().write(execute_base)
            self.handle(command)

    def handle_conditional_node(self, node: ConditionalNode):
        SUB_NODE_TO_STRING = {
            ConditionalNode.IfBlock: lambda node: f"block {position_to_str(node['pos'])} {node['block']}",
            ConditionalNode.IfEntity: lambda node: f"enitity {node['selector']}",
            ConditionalNode.IfPredicate: lambda node: f"predicate {node['val'].base}:{node['val'].path}",
            ConditionalNode.IfScore: lambda node: f"score {node['own'].value} {node['own'].scoreboard.unique_name} "
                                                  f"{node['relation'].value} {node['other'].value} {node['other'].scoreboard.unique_name}",
            ConditionalNode.IfScoreMatches: lambda node: f"score {node['own'].value} {node['own'].scoreboard.unique_name} "
                                                         f"matches {node['range']}"
        }

        sub_nodes = [("unless " if i.data.get("neg", False) else "if ") +
                     SUB_NODE_TO_STRING[type(i)](i) for i in node["conditions"]]
        if not sub_nodes:
            raise ValueError("Empty condition node")
        execute_base = f"execute {' '.join(sub_nodes)}"

        self.write_line(execute_base)

    def handle_if_node(self, node: IfNode):
        ...

    def handle_loop_node(self, node: LoopNode):
        ...

    def handle_store_fast_var_node(self, node: StoreFastVarNode):
        value = node["val"]
        variable = node["var"]
        init = node["init"]

        if isinstance(value, int):
            # if the value is zero, the operation can be omitted (if init is true).
            if value != 0 or not init:
                self.write_line(
                    f"scoreboard players set {variable.value} "
                    f"{variable.scoreboard.unique_name} {value}"
                )
        elif isinstance(value, ScoreboardValue):
            # scoreboard players operation a objective = b objective
            self.write_line(
                f"scoreboard players operation {variable.value} {variable.scoreboard.unique_name} "
                f"= {value.value} {value.scoreboard.unique_name}"
            )
        elif isinstance(value, DataPath):
            # execute store result score a objective run data get storage mcsscript:test a.b.c
            self.write_line(
                f"execute store result score {variable.value} {variable.scoreboard.unique_name} "
                f"run data get storage {value.storage.base}:{value.storage.path} {value.dotted_path()}"
            )
        else:
            raise ValueError(f"Unknown integer value source: {value}")

    def handle_store_fast_var_from_result_node(self, node: StoreFastVarFromResultNode):
        var = node["var"]
        self.files.get().write(
            f"execute store result score {var.value} {var.scoreboard.unique_name} run ")

        child, *error = node.inner_nodes
        if error:
            raise ValueError(f"Node {node} should only have one child!")

        self.handle(child)

    def handle_store_var_node(self, node: StoreVarNode):
        raise NotImplementedError()

    def handle_store_var_from_result_node(self, node: StoreVarFromResultNode):
        raise NotImplementedError()

    def handle_fast_var_operation_node(self, node: FastVarOperationNode):
        a = node["a"]
        b = node["b"]
        operator = node["operator"]

        # if b is an integer and this is not a subtraction or sum
        # use a constant to create a scoreboard value for b
        if isinstance(b, int) and operator not in (BinaryOperator.PLUS, BinaryOperator.MINUS):
            b = self._get_constant(b, a.scoreboard)

        if isinstance(b, ScoreboardValue):
            self.write_line(
                f"scoreboard players operation {a.value} {a.scoreboard.unique_name} "
                f"{operator.value}= {b.value} {b.scoreboard.unique_name}"
            )
        elif isinstance(b, int):
            # only defined for operations plus and minus
            if operator == BinaryOperator.MINUS:
                b *= -1

            mode = "add" if b >= 0 else "remove"

            self.write_line(
                f"scoreboard players {mode} {a.value} {a.scoreboard.unique_name} {b}"
            )
        else:
            raise ValueError(f"Invalid b value for operation: {b}")

    def handle_invert_node(self, node: InvertNode):
        raise NotImplementedError()

    def handle_message_node(self, node: MessageNode):
        message_type = node["type"]
        message = node["msg"]
        selector = node["selector"]

        if message_type == MessageNode.MessageType.CHAT:
            self.write_line(f"tellraw {selector} {message}")
        elif message_type == MessageNode.MessageType.TITLE:
            self.write_line(f"title {selector} title {message}")
        elif message_type == MessageNode.MessageType.SUBTITLE:
            self.write_line(f"title {selector} subtitle {message}")
        elif message_type == MessageNode.MessageType.ACTIONBAR:
            self.write_line(f"title {selector} actionbar {message}")
        else:
            raise ValueError(f"Unknown message type: {message_type}")

    def handle_command_node(self, node: CommandNode):
        self.write_line(node["cmd"])

    def handle_set_block_node(self, node: SetBlockNode):
        raise NotImplementedError()

    def handle_summon_node(self, node: SummonNode):
        raise NotImplementedError()

    def handle_kill_node(self, node: KillNode):
        raise NotImplementedError()

    def handle_scoreboard_init_node(self, node: ScoreboardInitNode):
        scoreboard = node["scoreboard"]
        self.write_line(
            f"scoreboard objectives remove {scoreboard.unique_name}")
        self.write_line(
            f"scoreboard objectives add {scoreboard.unique_name} dummy")
