from dataclasses import dataclass, field
from functools import cached_property
from typing import List

from mcscript import Logger


def _char_range(start, end) -> List[str]:
    return [chr(i) for i in range(ord(start), ord(end) + 1)]


VALID_OBJECTIVE_CHARACTERS = _char_range("0", "9") + _char_range("A", "Z") + _char_range("a", "z") + list("_-.+")


@dataclass
class Scoreboard:
    name: str
    use_real_name: bool
    index: int
    criteria: str = field(default="dummy")

    def __post_init__(self):
        if len(self.name) > 16:
            raise ValueError("Cannot create a scoreboard with a length > 16")
        if self.index >= len(VALID_OBJECTIVE_CHARACTERS) ** 3:
            raise ValueError(
                f"Maximum id exceeded: {self.index} expected at most {len(VALID_OBJECTIVE_CHARACTERS) ** 3 - 1}")
        Logger.debug(f"[Scoreboard] created {self.name} with id {self.get_name()}")

    def get_name(self) -> str:
        if self.use_real_name:
            return self.name
        return self.unique_name

    @cached_property
    def unique_name(self) -> str:
        """
        Converts `self.index` to a number base `len(self.index)` using the valid objective alphabet.
        A scoreboard name may have at most 16 characters. A mcscript scoreboard name may have at most 13 characters
        which means that three characters are left for scoreboard identifiers.
        66^3-1 = 287_495 which should be enough unique scoreboard names for most purposes
        """
        from mcscript.data.Config import Config

        out = []
        index = self.index
        while index >= len(VALID_OBJECTIVE_CHARACTERS):
            index, rest = divmod(index, len(VALID_OBJECTIVE_CHARACTERS))
            out.append(rest)
        out.append(index)
        return "{}.{}".format(
            Config.currentConfig.get_scoreboard("main"),
            "".join(VALID_OBJECTIVE_CHARACTERS[i] for i in reversed(out))
        )

    def __repr__(self) -> str:
        return f"Scoreboard({self.unique_name})"

    def __str__(self) -> str:
        return self.unique_name
