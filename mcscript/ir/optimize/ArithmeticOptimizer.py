from fractions import Fraction
from typing import List, Optional

from mcscript.ir import IRNode
from mcscript.ir.command_components import BinaryOperator
from mcscript.ir.components import FastVarOperationNode
from mcscript.ir.optimize.Optimizer import Optimizer

ADDITION = (BinaryOperator.PLUS, BinaryOperator.MINUS)
MULTIPLICATION = (BinaryOperator.TIMES, BinaryOperator.DIVIDE)


class ArithmeticOptimizer(Optimizer):
    """
    Optimizes redundant scoreboard operations.
    Example:
        var *= 2000
        var /= 1000
        =>
        var *= 2

        var += 50
        var += 60
        var -= 10
        =>
        var += 100

    These optimizations can often be applied on fixed point operations.

    ToDo: This code currently does not get optimized:
    var = dyn(2.0)
    foo = dyn(3.0)
    var = 2.0 * var + foo.

    This creates:
    scoreboard players operation .exp1_0 mcscript.0 *= #2 mcscript.0
    scoreboard players operation .exp1_0 mcscript.0 *= .exp1_1 mcscript.0
    scoreboard players operation .exp1_0 mcscript.0 /= #1000 mcscript.0
    """

    def optimize(self):
        for function in self.visit_top_functions():
            if len(function.inner_nodes) >= 2:
                could_optimize = True
                while could_optimize:
                    could_optimize = self.optimize_function(function.inner_nodes)

    def optimize_function(self, nodes: List[IRNode]) -> bool:
        """ Optimizes the nodes in a function. Returns true if an optimization could be made"""

        for i in range(1, len(nodes)):
            current = nodes[i - 1]

            if isinstance(current, FastVarOperationNode):
                if current["operator"] in MULTIPLICATION:
                    operation_type = MULTIPLICATION
                elif current["operator"] in ADDITION:
                    operation_type = ADDITION
                else:
                    continue

                interesting_nodes = []
                var = current["var"]
                j = i - 1
                while (
                        isinstance(current, FastVarOperationNode)
                        and current["operator"] in operation_type
                        and current["var"] == var
                ):
                    if isinstance(current["b"], int):
                        interesting_nodes.append(j)
                    j += 1
                    if j >= len(nodes):
                        break
                    current = nodes[j]

                if len(interesting_nodes) < 2:
                    continue

                if operation_type == MULTIPLICATION:
                    result = self.optimize_multiplication_nodes(nodes, interesting_nodes)
                elif operation_type == ADDITION:
                    result = self.optimize_addition_nodes(nodes, interesting_nodes)
                else:
                    raise ValueError

                if result is not None:
                    for index in reversed(result):
                        del nodes[index]
                    return True

    def optimize_multiplication_nodes(self, nodes: List[IRNode], indices: List[int]) -> Optional[List[int]]:
        product = Fraction(1, 1)
        first_index = indices[0]
        for index in indices:
            node = nodes[index]
            if node["operator"] == BinaryOperator.DIVIDE:
                product *= Fraction(1, node["b"])
            else:
                product *= Fraction(node["b"], 1)

        to_drop = indices[1:]
        if product.denominator == 1:
            # if just multiply by one, drop all nodes
            if product.numerator == 1:
                return indices
            nodes[first_index]["operator"] = BinaryOperator.TIMES
            nodes[first_index]["b"] = product.numerator
            return to_drop

        inv = 1 / product
        if inv.denominator == 1 and inv.numerator <= 1000:
            nodes[first_index]["operator"] = BinaryOperator.DIVIDE
            nodes[first_index]["b"] = inv.numerator
            return to_drop

    def optimize_addition_nodes(self, nodes: List[IRNode], indices: List[int]) -> Optional[List[int]]:
        total = 0
        for index in indices:
            node = nodes[index]
            if node["operator"] == BinaryOperator.PLUS:
                total += node["b"]
            else:
                total -= node["b"]

        # if the total is zero, drop all nodes
        if total == 0:
            return indices

        keep_node = nodes[indices[0]]
        to_drop = indices[1:]
        if total > 0:
            keep_node["operator"] = BinaryOperator.PLUS
        else:
            keep_node["operator"] = BinaryOperator.MINUS
        keep_node["b"] = total
        return to_drop

# # match statements could really make this nicer
# if isinstance(current, FastVarOperationNode) and isinstance(peek, FastVarOperationNode):
#     # both nodes must operate on the same variable
#     if current["var"] == peek["var"]:
#         # both nodes must hold an integer
#         if isinstance(current["b"], int) and isinstance(peek["b"], int):
#             # match on either (+, -) or (*, /)
#             if current["operator"] in MULTIPLICATION and peek["operator"] in MULTIPLICATION:
#                 # Use fraction to ensure no rounding errors occur
#                 if current["operator"] == BinaryOperator.DIVIDE:
#                     a = Fraction(1, current["b"])
#                 else:
#                     a = Fraction(current["b"], 1)
#
#                 if peek["operator"] == BinaryOperator.DIVIDE:
#                     b = Fraction(1, peek["b"])
#                 else:
#                     b = Fraction(peek["b"], 1)
#
#                 result = a * b
#                 # If the result is still an integer
#                 if result.denominator == 1:
#                     del nodes[i]
#                     nodes[i - 1]["b"] = result.numerator
#                     nodes[i - 1]["operator"] = BinaryOperator.TIMES
#                     return True
#
#                 # This code might problematic if it can lead to rounding errors
#                 # Todo: verify that is doesnt
#                 inv = 1 / result
#                 if inv.denominator == 1:
#                     del nodes[i]
#                     nodes[i - 1]["b"] = inv.numerator
#                     nodes[i - 1]["operator"] = BinaryOperator.DIVIDE
#                     return True
#
#                 if Logger.isEnabledFor(DEBUG):
#                     Logger.debug(f"[ArithmeticOptimizer] Could not optimize {result}: Not an integer")
#             elif current["operator"] in ADDITION and peek["operator"] in ADDITION:
#                 a = current["b"]
#                 if current["operator"] == BinaryOperator.MINUS:
#                     a *= -1
#
#                 b = peek["b"]
#                 if current["operator"] == BinaryOperator.MINUS:
#                     b *= -1
#
#                 del nodes[i]
#                 nodes[i - 1]["b"] = a + b
#                 return True
#
# current = peek
