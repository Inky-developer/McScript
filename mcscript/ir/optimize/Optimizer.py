from abc import abstractmethod, ABC

from mcscript.ir.NodeVisitor import NodeVisitor


class Optimizer(NodeVisitor, ABC):
    @abstractmethod
    def optimize(self):
        """
        Optimize the node tree starting at the start node in place

        Returns:
            None
        """
        ...
