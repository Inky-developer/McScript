from typing import List, Type

from mcscript.ir.components import FunctionNode
from mcscript.ir.optimize.ArithmeticOptimizer import ArithmeticOptimizer
from mcscript.ir.optimize.Optimizer import Optimizer

OPTIMIZERS: List[Type[Optimizer]] = [ArithmeticOptimizer]


def optimize(start_node: FunctionNode, nodes: List[FunctionNode]):
    """
    Applies all `OPTIMIZERS` on the nodes

    Args:
        start_node: The node at which control flow starts
        nodes: All top level function nodes

    Returns:
        None, modifies in place
    """
    function_nodes = {node["name"]: node for node in nodes}
    for ThisOptimizer in OPTIMIZERS:
        ThisOptimizer(start_node, function_nodes).optimize()
