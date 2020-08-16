from __future__ import annotations

from contextlib import contextmanager
from typing import Dict, Optional

from mcscript.backends.IRBackend import IRBackend
from mcscript.backends.mc_datapack_backend import get_resource
from mcscript.backends.mc_datapack_backend.Datapack import Datapack
from mcscript.backends.mc_datapack_backend.runtime import make_on_load_function
from mcscript.backends.mc_datapack_backend.utils import position_to_str
from mcscript.data.Config import Config
from mcscript.ir.components import *
from mcscript.utils.resources import Identifier


class McDatapackBackend(IRBackend[Datapack]):
    def __init__(self, config: Config, ir_master: IrMaster):
        super().__init__(config, ir_master)

        self.datapack = Datapack(self.config)
        self.files = self.datapack.getMainDirectory().getPath("functions").files

        # A List of pending commands
        self.command_buffer: List[List[str]] = []

        # A list of all constants used by this backend
        self.constant_scores: Dict[int, ScoreboardValue] = {}

        self.on_tick_function: Optional[FunctionNode] = None
        self.on_load_function: Optional[FunctionNode] = None

    def _get_constant(self, value: int, scoreboard: Scoreboard) -> ScoreboardValue:
        if value in self.constant_scores:
            return self.constant_scores[value]

        scoreboard_value = ScoreboardValue(
            Identifier(f"#{value}"),
            scoreboard
        )

        self.constant_scores[value] = scoreboard_value
        return scoreboard_value

    @contextmanager
    def assemble_command(self):
        """
        Assembles a single command from multiple nodes
        """
        temp = []
        self.command_buffer.append(temp)
        try:
            yield temp
        finally:
            self.command_buffer.pop()

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
        init_constants_fn = FunctionNode(self.config.resource_specifier_main("init_constants"),
                                         nodes) if nodes else None

        init_scoreboards_fn = FunctionNode(
            self.config.resource_specifier_main("init_scoreboards"),
            [ScoreboardInitNode(i) for i in self.ir_master.scoreboards]
        ) if self.ir_master.scoreboards else None

        load_fn = make_on_load_function(self.on_load_function, self, init_constants_fn, init_scoreboards_fn)
        self.handle(load_fn)
        load_json = self.datapack.get_minecraft_directory().getPath("tags/functions").addFile("load.json")
        load_json.write(get_resource("load.json").format(load_fn["name"]))

        if self.on_tick_function is not None:
            tick_json = self.datapack.get_minecraft_directory().getPath("tags/functions").addFile("tick.json")
            tick_json.write(get_resource("tick.json").format(self.on_tick_function["name"]))

    def handle_function_node(self, node: FunctionNode):
        # This is temporary
        if node["name"].path == "on_tick":
            self.on_tick_function = node
        elif node["name"].path == "main":
            self.on_load_function = node

        self.files.push(f"{node['name'].path}.mcfunction")
        for child in node.inner_nodes:
            self.command_buffer.append([])
            self.handle(child)

        for command in self.command_buffer:
            for line in command:
                self.write_line(line)
        self.command_buffer.clear()

    def handle_function_call_node(self, node: FunctionCallNode):
        function = node["function"]
        value = function["name"]
        self.command_buffer[-1].append(
            f"function {value.base}:{value.path}"
        )

    def handle_execute_node(self, execute: ExecuteNode):
        SUB_NODE_TO_STRING = {
            ExecuteNode.As: lambda node: f"as {node['selector']}",
            ExecuteNode.At: lambda node: f"at {node['selector']}",
            ExecuteNode.Positioned: lambda node: f"positioned {position_to_str(node['pos'])}",
            ExecuteNode.Anchored: lambda node: f"anchored {node['anchor'].value}"
        }

        sub_nodes = [SUB_NODE_TO_STRING[type(i)](
            i) for i in execute["components"]]
        if not sub_nodes:
            raise ValueError("Empty execute node")
        execute_base = f"execute {' '.join(sub_nodes)} run"

        # ToDO: when optimizing, create a new file for multiple inner nodes
        for command in execute.inner_nodes:
            with self.assemble_command() as parts:
                self.command_buffer[-1].append(execute_base)
                self.handle(command)
            base, command = parts
            self.command_buffer[-1].append(f"{base} {command}")

    def handle_conditional_node(self, conditional: ConditionalNode):
        def if_score_matches(node):
            return f"score {node['own']} matches {node['range']}"

        def if_score(node):
            return f"score {node['own']} {node['relation'].value} {node['other']}"

        SUB_NODE_TO_STRING = {
            ConditionalNode.IfBlock: lambda node: f"block {position_to_str(node['pos'])} {node['block']}",
            ConditionalNode.IfEntity: lambda node: f"entity {node['selector']}",
            ConditionalNode.IfPredicate: lambda node: f"predicate {node['val'].base}:{node['val'].path}",
            ConditionalNode.IfScore: if_score,
            ConditionalNode.IfScoreMatches: if_score_matches
        }

        sub_nodes = [("unless " if i.data.get("neg", False) else "if ") +
                     SUB_NODE_TO_STRING[type(i)](i) for i in conditional["conditions"]]
        if not sub_nodes:
            raise ValueError("Empty condition node")
        execute_base = f"execute {' '.join(sub_nodes)}"

        self.command_buffer[-1].append(execute_base)

    def handle_if_node(self, node: IfNode):
        def assemble_branch(branch: IRNode):
            with self.assemble_command() as parts:
                self.handle(condition)
                self.handle(branch)

            execute, command = parts
            self.command_buffer[-1].append(f"{execute} run {command}")

        condition: ConditionalNode = node["condition"]
        pos_branch, neg_branch = node.pos_branch, node.neg_branch

        assemble_branch(pos_branch)

        if neg_branch:
            condition.invert()
            assemble_branch(neg_branch)

    def handle_get_fast_var_node(self, node: GetFastVarNode):
        val = node["val"]
        self.command_buffer[-1].append(f"scoreboard players get {val}")

    def handle_store_fast_var_node(self, node: StoreFastVarNode):
        value = node["val"]
        variable = node["var"]

        if isinstance(value, int):
            self.command_buffer[-1].append(
                f"scoreboard players set {variable} {value}"
            )
        elif isinstance(value, ScoreboardValue):
            # scoreboard players operation a objective = b objective
            self.command_buffer[-1].append(
                f"scoreboard players operation {variable} "
                f"= {value}"
            )
        elif isinstance(value, DataPath):
            # execute store result score a objective run data get storage mcscript:test a.b.c
            self.command_buffer[-1].append(
                f"execute store result score {variable} "
                f"run data get storage {value.storage.base}:{value.storage.path} {value.dotted_path()}"
            )
        else:
            raise ValueError(f"Unknown integer value source: {value}")

    def handle_store_fast_var_from_result_node(self, node: StoreFastVarFromResultNode):
        var = node["var"]

        with self.assemble_command() as parts:
            self.command_buffer[-1].append(
                f"execute store result score {var} run")

            child, *error = node.inner_nodes
            if error:
                raise ValueError(f"Node {node} should only have one child!")

            self.handle(child)

        execute, command = parts
        self.command_buffer[-1].append(f"{execute} {command}")

    def handle_store_var_node(self, node: StoreVarNode):
        raise NotImplementedError()

    def handle_store_var_from_result_node(self, node: StoreVarFromResultNode):
        var = node["var"]
        dtype = node["dtype"]
        scale = node["scale"]

        with self.assemble_command() as parts:
            self.command_buffer[-1].append(
                f"execute store result storage {var.storage} {var.dotted_path()} {dtype.value} {scale} run")
            self.handle_children(node)

        base, command = parts
        self.command_buffer[-1].append(f"{base} {command}")

    def handle_fast_var_operation_node(self, node: FastVarOperationNode):
        a = node["var"]
        b = node["b"]
        operator = node["operator"]

        # if b is an integer and this is not a subtraction or sum
        # use a constant to create a scoreboard value for b
        if isinstance(b, int) and operator not in (BinaryOperator.PLUS, BinaryOperator.MINUS):
            b = self._get_constant(b, a.scoreboard)

        self.handle_children(node)

        if isinstance(b, ScoreboardValue):
            self.command_buffer[-1].append(
                f"scoreboard players operation {a} "
                f"{operator.value}= {b}"
            )
        elif isinstance(b, int):
            # only defined for operations plus and minus
            if operator == BinaryOperator.MINUS:
                b *= -1

            mode = "add" if b >= 0 else "remove"

            self.command_buffer[-1].append(
                f"scoreboard players {mode} {a} {abs(b)}"
            )
        else:
            raise ValueError(f"Invalid b value for operation: {b}")

    def handle_invert_node(self, node: InvertNode):
        target = node["target"]
        value = node["val"]
        self.handle(StoreFastVarFromResultNode(
            target,
            ConditionalNode([ConditionalNode.IfScoreMatches(value, ScoreRange(0), False)])
        ))

    def handle_message_node(self, node: MessageNode):
        message_type = node["type"]
        message = node["msg"]
        selector = node["selector"]

        if message_type == MessageNode.MessageType.CHAT:
            self.command_buffer[-1].append(f"tellraw {selector} {message}")
        elif message_type == MessageNode.MessageType.TITLE:
            self.command_buffer[-1].append(f"title {selector} title {message}")
        elif message_type == MessageNode.MessageType.SUBTITLE:
            self.command_buffer[-1].append(f"title {selector} subtitle {message}")
        elif message_type == MessageNode.MessageType.ACTIONBAR:
            self.command_buffer[-1].append(f"title {selector} actionbar {message}")
        else:
            raise ValueError(f"Unknown message type: {message_type}")

    def handle_command_node(self, node: CommandNode):
        self.command_buffer[-1].append(node["cmd"])

    def handle_set_block_node(self, node: SetBlockNode):
        raise NotImplementedError()

    def handle_summon_node(self, node: SummonNode):
        raise NotImplementedError()

    def handle_kill_node(self, node: KillNode):
        raise NotImplementedError()

    def handle_scoreboard_init_node(self, node: ScoreboardInitNode):
        scoreboard = node["scoreboard"]
        self.command_buffer[-1].append(
            f"scoreboard objectives remove {scoreboard.get_name()}")
        self.command_buffer[-1].append(
            f"scoreboard objectives add {scoreboard.get_name()} dummy")
