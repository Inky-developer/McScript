from __future__ import annotations

from enum import Enum, auto
from typing import List, Union, TYPE_CHECKING, Tuple

from mcscript.data.minecraftData.blocks import Block, BlockstateBlock
from mcscript.data.selector.Selector import Selector
from mcscript.ir import IRNode
from mcscript.ir.command_components import Position, ExecuteAnchor, ScoreRelation, ScoreRange, BinaryOperator
from mcscript.utils.Scoreboard import Scoreboard
from mcscript.utils.resources import ResourceSpecifier, Identifier, ScoreboardValue, DataPath

if TYPE_CHECKING:
    from mcscript.ir.IrMaster import IrMaster


class FunctionNode(IRNode):
    """
    A nodes that contains various other nodes which can be serialized to a mcfunction file
    """

    def __init__(self, name: Identifier, children: List[IRNode]):
        super().__init__(children)
        self["name"] = name
        # whether the function is dead code and can be dropped
        self["drop"] = False


class FunctionCallNode(IRNode):
    """
    A mcfunction call
    """

    def __init__(self, function_name: ResourceSpecifier):
        super().__init__()
        self["name"] = function_name

    def optimized(self, ir_master: IrMaster, parent: IRNode) -> Tuple[IRNode, bool]:
        if function_node := ir_master.find_function_node(self["name"]):
            # inline if the called function only has one child
            if len(function_node.inner_nodes) == 1:
                node = function_node.inner_nodes[0]
                if node.allow_inline_optimization():
                    # Drop this node because it will be inlined everywhere
                    function_node["drop"] = True
                    return node, True

        return super().optimized(ir_master, parent)


class ExecuteNode(IRNode):
    """
    An execute function. Can have multiple components and a sub-node.
    """

    class As(IRNode):
        def __init__(self, selector: Selector):
            super().__init__()
            self["selector"] = selector

    class At(IRNode):
        def __init__(self, selector: Selector):
            super().__init__()
            self["selector"] = selector

    class Positioned(IRNode):
        def __init__(self, position: Position):
            super().__init__()
            self["pos"] = position

    class Anchored(IRNode):
        def __init__(self, anchor: ExecuteAnchor):
            super().__init__()
            self["anchor"] = anchor

    ExecuteArgument = Union[As, At, Positioned, Anchored]

    def __init__(self, components: List[ExecuteArgument], sub_commands: List[IRNode]):
        super().__init__(sub_commands)
        self["components"] = components

    def optimized(self, ir_master: IrMaster, parent: IRNode) -> Tuple[IRNode, bool]:
        components = self["components"]
        children = self.inner_nodes

        # inline message node
        if len(components) == 1 and isinstance(components[0], self.As):
            if len(children) == 1 and isinstance(children[0], MessageNode):
                if children[0]["selector"] == Selector("s", []) and children[0].allow_inline_optimization():
                    children[0]["selector"] = components[0]["selector"]
                    return children[0], True

        return super().optimized(ir_master, parent)


class ConditionalNode(IRNode):
    class IfScore(IRNode):
        def __init__(self, own_score: ScoreboardValue, other_score: ScoreboardValue, relation: ScoreRelation,
                     neg: bool = False):
            super().__init__()
            self["own"] = own_score
            self["other"] = other_score
            self["relation"] = relation
            self["neg"] = neg

    class IfScoreMatches(IRNode):
        def __init__(self, own_score: ScoreboardValue, range_: ScoreRange, negate: bool):
            super().__init__()
            self["own"] = own_score
            self["range"] = range_
            self["neg"] = negate

    class IfBlock(IRNode):
        def __init__(self, position: Position, block: Block, negate: bool):
            super().__init__()
            self["pos"] = position
            self["block"] = block
            self["neg"] = negate

    class IfEntity(IRNode):
        def __init__(self, selector: Selector, negate: bool):
            super().__init__()
            self["selector"] = selector
            self["neg"] = negate

    class IfPredicate(IRNode):
        def __init__(self, predicate: ResourceSpecifier, negate: bool):
            super().__init__()
            self["val"] = predicate
            self["neg"] = negate

    # If the condition could be evaluated at compile time
    class IfBool(IRNode):
        def __init__(self, boolean: bool):
            super().__init__()
            self["val"] = boolean

    ConditionalArgument = Union[IfScore, IfScoreMatches,
                                IfBlock, IfEntity, IfPredicate, IfBool]

    def __init__(self, conditions: List[ConditionalArgument]):
        super().__init__([])
        self["conditions"] = conditions

    def invert(self):
        if len(self["conditions"]) > 1:
            raise ValueError("This is deprecated. Just use one condition")
        self["conditions"][0]["neg"] = not self["conditions"][0]["neg"]


class IfNode(IRNode):
    # class _PosBranch(IRNode):
    #     def __init__(self, commands: List[IRNode]):
    #         super().__init__(commands)
    #
    # class _NegBranch(IRNode):
    #     def __init__(self, commands: List[IRNode]):
    #         super().__init__(commands)

    def __init__(self, condition: ConditionalNode, pos_branch: IRNode, neg_branch: IRNode = None):
        nodes = [pos_branch]
        if neg_branch is not None:
            nodes.append(neg_branch)
        super().__init__(nodes)
        self["condition"] = condition

    @property
    def pos_branch(self):
        return self.inner_nodes[0]

    @property
    def neg_branch(self):
        return None if len(self.inner_nodes) < 2 else self.inner_nodes[1]

    def allow_inline_optimization(self) -> bool:
        # inline of no else branch exists
        return self.neg_branch is None

    def optimized(self, ir_master: IrMaster, parent: IRNode) -> Tuple[IRNode, bool]:
        # Check if the previous node is a ´StoreFastVarFromResultNode´ and contains a ´ConditionalNode´
        # if so, we can replace this condition with the condition of the previous node
        index = -1
        for index, node in enumerate(parent.inner_nodes):
            if node is self:
                break
        prev_node_index = index - 1
        if prev_node_index >= 0:
            prev_node = parent.inner_nodes[prev_node_index]
            if isinstance(prev_node, StoreFastVarFromResultNode):
                if len(prev_node.inner_nodes) == 1 and isinstance(prev_node.inner_nodes[0], ConditionalNode):
                    if prev_node.allow_inline_optimization():
                        parent.discarded_inner_nodes.append(prev_node)
                        self["condition"] = prev_node.inner_nodes[0]
                        return self, True

        return super().optimized(ir_master, parent)


####
# Fast Variables are stored in a scoreboard
####

NumericalNumberSource = Union[int, DataPath, ScoreboardValue]


class StoreFastVarNode(IRNode):
    def __init__(self, scoreboard_value: ScoreboardValue, value: NumericalNumberSource):
        super().__init__()
        self["var"] = scoreboard_value
        self["val"] = value


class StoreFastVarFromResultNode(IRNode):
    """ Stores a value returned by execute into a scoreboard. """

    def __init__(self, scoreboard_value: ScoreboardValue, command: IRNode):
        super().__init__([command])
        self["var"] = scoreboard_value


####
# 'Normal' Variables are stored in a data storage
####

class StoreVarNode(IRNode):
    def __init__(self, storage: DataPath, value: NumericalNumberSource):
        super().__init__()
        self["var"] = storage
        self["val"] = value


class StoreVarFromResultNode(IRNode):
    def __init__(self, storage: DataPath, command: IRNode):
        super().__init__([command])
        self["var"] = storage


class FastVarOperationNode(IRNode):
    """
    performs the operation in-place on a.
    b may be either another scoreboard value or an integer
    """

    def __init__(self, a: ScoreboardValue, b: Union[int, ScoreboardValue], operator: BinaryOperator):
        super().__init__()
        self["a"] = a
        self["b"] = b
        self["operator"] = operator


####
class InvertNode(IRNode):
    """ Stores 1 in target if val is zero, otherwise 0. """

    def __init__(self, val: ScoreboardValue, target: ScoreboardValue):
        super().__init__()
        self["val"] = val
        self["target"] = target


####


class MessageNode(IRNode):
    """
    Json message. The default selector is @s.
    """

    class MessageType(Enum):
        CHAT = auto()
        TITLE = auto()
        SUBTITLE = auto()
        ACTIONBAR = auto()

    def __init__(self, msg_type: MessageType, msg: str, selector: Selector = None):
        super().__init__()
        self["type"] = msg_type
        self["msg"] = msg
        self["selector"] = selector or Selector("s", [])


class CommandNode(IRNode):
    """ Translates directly to its parameter string. """

    def __init__(self, command: str):
        super().__init__()
        self["cmd"] = command


####
# From now on mostly wrappers for general minecraft command
####

class SetBlockNode(IRNode):
    def __init__(self, position: Position, block: BlockstateBlock, nbt: str = None):
        # ToDo: use nbt class
        super().__init__()
        self["pos"] = position
        self["block"] = block
        self["nbt"] = nbt


class SummonNode(IRNode):
    def __init__(self, entity: str, position: Position):
        super().__init__()
        # ToDo: use entity class
        self["entity"] = entity
        self["pos"] = position


class KillNode(IRNode):
    def __init__(self, selector: Selector):
        super().__init__()
        self["selector"] = selector


class ScoreboardInitNode(IRNode):
    def __init__(self, scoreboard: Scoreboard):
        super().__init__()
        self["scoreboard"] = scoreboard

    def allow_inline_optimization(self) -> bool:
        return False
