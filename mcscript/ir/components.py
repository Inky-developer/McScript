from enum import Enum, auto
from typing import List, Union, Any

from mcscript.data.Scoreboard import Scoreboard
from mcscript.data.minecraftData.blocks import Block, BlockstateBlock
from mcscript.data.selector.Selector import Selector
from mcscript.ir import IRNode
from mcscript.ir.command_components import Position, ExecuteAnchor, Identifier, ScoreboardValue, DataPath, \
    ScoreRelation, ScoreRange, BooleanOperator
from mcscript.ir.data import NumericalNumberSource
from mcscript.utils.resourceSpecifier import ResourceSpecifier


class FunctionNode(IRNode):
    """
    A nodes that contains various other nodes which can be serialized to a mcfunction file
    """

    def __init__(self, name: ResourceSpecifier, children: List[IRNode]):
        super().__init__(children)
        self["name"] = name


class FunctionCallNode(IRNode):
    """
    A mcfunction call
    """

    def __init__(self, function_name: ResourceSpecifier):
        super().__init__()
        self["name"] = function_name


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

    # Unless scored not needed (just invert IfScore relation)
    class IfScore(IRNode):
        def __init__(self, own_score: ScoreboardValue, other_score: ScoreboardValue, relation: ScoreRelation):
            super().__init__()
            self["own"] = own_score
            self["other"] = other_score
            self["relation"] = relation

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

    ExecuteArgument = Union[As, At, Positioned, Anchored, IfScore, IfScoreMatches, IfBlock, IfEntity, IfPredicate]

    def __init__(self, components: List[ExecuteArgument], sub_commands: List[IRNode]):
        super().__init__(sub_commands)
        self["components"] = components


####
# Fast Variables are stored in a scoreboard
####

# class _GetFastVarNode(IRNode):
#     """ ***Returns*** a scoreboard value. """
#
#     def __init__(self, scoreboard_value: ScoreboardValue):
#         super().__init__()
#         self["var"] = scoreboard_value


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

# class _GetVarNode(IRNode):
#     """ ***Returns*** a value from a data storage.  """
#
#     def __init__(self, storage: DataPath):
#         super().__init__()
#         self["storage"] = DataPath


class StoreVarNode(IRNode):
    def __init__(self, storage: DataPath, value: Any):
        super().__init__()
        self["var"] = storage
        self["val"] = value


class StoreVarFromResultNode(IRNode):
    def __init__(self, storage: DataPath, command: IRNode):
        super().__init__([command])
        self["var"] = storage


class FastVarOperationNode(IRNode):
    def __init__(self, a: ScoreboardValue, b: ScoreboardValue, operator: BooleanOperator):
        super().__init__()
        self["a"] = a
        self["b"] = b
        self["operator"] = operator


class MessageNode(IRNode):
    class MessageType(Enum):
        CHAT = auto()
        TITLE = auto()
        SUBTITLE = auto()
        ACTIONBAR = auto()

    def __init__(self, msg_type: MessageType, msg: str):
        super().__init__()
        self["type"] = msg_type
        self["msg"] = msg


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


if __name__ == '__main__':
    f = FunctionNode(
        ResourceSpecifier("mcscript", "test_function"),
        [
            IRNode(code="execute('test')"),
            FunctionCallNode(ResourceSpecifier("mcscript", "test_2")),
            ExecuteNode([ExecuteNode.As(Selector("a", [])), ExecuteNode.At(Selector("s", []))],
                        [StoreFastVarNode(ScoreboardValue(Identifier("mcscript"), Scoreboard("test", True, 0)), 15)]),
            StoreVarFromResultNode(DataPath(ResourceSpecifier("mcscript", "main"), ["state", "vars"]), IRNode()),
            ExecuteNode([ExecuteNode.IfScoreMatches(ScoreboardValue(Identifier("test"), Scoreboard("test", True, 1)),
                                                    ScoreRange(float("10"), float("20")))], [IRNode()])
        ]
    )
    print(f)
