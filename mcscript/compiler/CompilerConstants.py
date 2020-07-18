from __future__ import annotations

from typing import Dict, TYPE_CHECKING

from mcscript.ir.components import StoreFastVarNode
from mcscript.utils.Scoreboard import Scoreboard
from mcscript.utils.resources import ScoreboardValue, Identifier

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class CompilerConstants:
    """
    During compile time some numeric values are being used multiple times.
    A good example are fixed-point numbers. When multiplying fixed-number a by fixed number b, first their integer
    values get multiplied and this result then gets divide by 1000 (BASE). Because Minecraft only supports arithmetic
    operations with scoreboard values (there are some exceptions) the numeric value 1000 would have to be store on a
    scoreboard. This is problematic because I designed the scoreboard expression system as a "throwaway" system which
    uses a value only for a single operation and then discards it. This has some advantages but also means that for
    every single fixed-number multiplication the value 1000 would have to be stored on a scoreboard and there are
    many other cases which are similar.

    To improve on that, this class will keep a list of compile-time constants (like 1000 for `FixedNumber.BASE`)
    and their corresponding scoreboard addresses. These are kept throughout the entire programs lifetime and prefixed
    with .const instead of .exp.
    """

    def __init__(self, scoreboard: Scoreboard, stackFmt: str = ".const_{}"):
        self.scoreboard = scoreboard
        self.stackFmt = stackFmt
        self.cache: Dict[int, str] = {}

    def get_constant(self, constant: int) -> ScoreboardValue:
        """
        Returns a stack address of a player who has the score specified in `constant`.
        This address is not unique and should not be modified.

        Args:
            constant: the numerical constant value

        Returns:
            A str which is the name of the player with the requested score.
        """
        if constant not in self.cache:
            self.cache[constant] = self.stackFmt.format(constant)

        return ScoreboardValue(Identifier(self.cache[constant]), self.scoreboard)

    def write_constants(self, compileState: CompileState):
        """
        Writes all constants that are currently in the cache to the current open file in compile state

        Args:
            compileState: the compile state
        """

        for number in sorted(self.cache):
            compileState.ir.append(StoreFastVarNode(
                self.get_constant(number),
                number
            ))
