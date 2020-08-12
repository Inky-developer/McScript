from fractions import Fraction
from logging import DEBUG
from typing import List

from mcscript import Logger
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
    """

    def optimize(self):
        for function in self.visit_top_functions():
            if len(function.inner_nodes) >= 2:
                could_optimize = True
                while could_optimize:
                    could_optimize = self.optimize_function(function.inner_nodes)

    def optimize_function(self, nodes: List[IRNode]) -> bool:
        """ Optimizes the nodes in a function. Returns true if an optimization could be made"""
        current = nodes[0]

        for i in range(1, len(nodes)):
            peek = nodes[i]

            # match statements could really make this nicer
            if isinstance(current, FastVarOperationNode) and isinstance(peek, FastVarOperationNode):
                # both nodes must operate on the same variable
                if current["var"] == peek["var"]:
                    # both nodes must hold an integer
                    if isinstance(current["b"], int) and isinstance(peek["b"], int):
                        # match on either (+, -) or (*, /)
                        if current["operator"] in MULTIPLICATION and peek["operator"] in MULTIPLICATION:
                            # Use fraction to ensure no rounding errors occur
                            if current["operator"] == BinaryOperator.DIVIDE:
                                a = Fraction(1, current["b"])
                            else:
                                a = Fraction(current["b"], 1)

                            if peek["operator"] == BinaryOperator.DIVIDE:
                                b = Fraction(1, peek["b"])
                            else:
                                b = Fraction(peek["b"], 1)

                            result = a * b
                            # If the result is still an integer
                            if result.denominator == 1:
                                del nodes[i]
                                nodes[i - 1]["b"] = result.numerator
                                nodes[i - 1]["operator"] = BinaryOperator.TIMES
                                return True

                            # This code might problematic if it can lead to rounding errors
                            # Todo: verify that is doesnt
                            inv = 1 / result
                            if inv.denominator == 1:
                                del nodes[i]
                                nodes[i - 1]["b"] = inv.numerator
                                nodes[i - 1]["operator"] = BinaryOperator.DIVIDE
                                return True

                            if Logger.isEnabledFor(DEBUG):
                                Logger.debug(f"[ArithmeticOptimizer] Could not optimize {result}: Not an integer")
                        elif current["operator"] in ADDITION and peek["operator"] in ADDITION:
                            a = current["b"]
                            if current["operator"] == BinaryOperator.MINUS:
                                a *= -1

                            b = peek["b"]
                            if current["operator"] == BinaryOperator.MINUS:
                                b *= -1

                            del nodes[i]
                            nodes[i - 1]["b"] = a + b
                            return True

            current = peek
