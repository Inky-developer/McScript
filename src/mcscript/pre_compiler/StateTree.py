from lark import Tree

from src.mcscript.data.builtins.builtins import BuiltinFunction

BadStatements = (
    "function_call",  # The PreCompiler will check if this function can be resolved
    "control_execute",
)


class StateTree(Tree):
    """
    Custom Tree class. This tree stores whether all subtrees and itself are determined at compile time so
    they can be reduced.
    """

    def __init__(self, data, children, meta=None):
        super().__init__(data, children, meta)

        self.isDetermined = all(
            child.isDetermined for child in self.children if isinstance(child, StateTree)
        ) and self._isDetermined()

    def _isDetermined(self) -> bool:
        """
        returns whether this tree can be determined (without checking children)
        """
        return self.data not in BadStatements and (
                self.data != "function_call" or self.children[0] not in (i.name() for i in
                                                                         BuiltinFunction.functions))
