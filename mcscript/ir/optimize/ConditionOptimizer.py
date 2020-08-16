from mcscript.ir import IRNode
from mcscript.ir.components import StoreFastVarFromResultNode, ConditionalNode, FunctionNode, IfNode
from mcscript.ir.optimize.Optimizer import Optimizer


def writes_condition_node(node: IRNode):
    return isinstance(node, StoreFastVarFromResultNode) and len(node.inner_nodes) == 1 and isinstance(
        node.inner_nodes[0], ConditionalNode)


class ConditionOptimizer(Optimizer):
    """
    Optimizes conditions.

    It is quite common to store a condition into a variable:
        val = evaluate_condition(...)

    Then, later, it is checked if the value matches 1
        if val == 1 run ...

    The temporary val can be ignored if:
        * The value is never written to until the condition is evaluated
        * The condition of the value only contains other values that do not change until the condition is evaluated
    """

    def optimize(self):
        for function in self.visit_top_functions():
            could_optimize = True
            while could_optimize:
                for index, node in enumerate(function.inner_nodes):
                    if writes_condition_node(node):
                        # noinspection PyTypeChecker
                        if self.try_optimize(index, node, function):
                            break
                else:
                    could_optimize = False

    def try_optimize(self, index: int, node: StoreFastVarFromResultNode, function: FunctionNode) -> bool:
        value = node["var"]
        original_condition = node.inner_nodes[0]
        depending_values = node.inner_nodes[0].read_scoreboard_values()
        could_optimize = False

        for i in range(index + 1, len(function.inner_nodes)):
            current = function.inner_nodes[i]

            # If any of the values that are read-only gets modified, optimization becomes impossible
            if any(i in current.written_scoreboard_values() for i in depending_values):
                return False

            if current.writes_scoreboard_value(value):
                return False

            if isinstance(current, IfNode):
                conditions = current["condition"]["conditions"]
                for index, j in enumerate(conditions):
                    if isinstance(j, ConditionalNode.IfScoreMatches) and j.reads_scoreboard_value(value):
                        # substitute the original condition
                        # If the value is negate, dont optimize for now
                        if not j.checks_if_true():
                            continue

                        # substitute the original condition
                        current["condition"]["conditions"] = \
                            conditions[:index] + original_condition["conditions"] + conditions[index + 1:]
                        could_optimize = True

        return could_optimize
