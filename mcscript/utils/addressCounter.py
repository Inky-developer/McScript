from __future__ import annotations

from mcscript.utils.Scoreboard import Scoreboard
from mcscript.utils.resources import ScoreboardValue, Identifier, DataPath


class AddressCounter:
    """
    A counter which formats the current value.
    Used to generate identifiers.
    """

    def __init__(self, fmt_string: str = "{}", default: int = 0):
        self.fmt_str = fmt_string
        self.value = self.default = default

    def getValue(self) -> str:
        return self.fmt_str.format(self.value)

    def next(self) -> str:
        val = self.getValue()
        self.value += 1
        return val

    def previous(self) -> str:
        self.value -= 1
        if self.value < 0:
            raise ValueError("Value of address must not be less than zero")
        return self.getValue()

    def decrement(self, n: int):
        self.value -= n
        if n < 0:
            raise ValueError("Value of address mus not be less than zero")

    def reset(self):
        self.value = self.default

    def clone(self) -> AddressCounter:
        a = AddressCounter(self.fmt_str, self.default)
        a.value = self.value
        return a


class ScoreboardAddressCounter(AddressCounter):
    """
    A counter which formats the current value.
    Used to generate identifiers for scoreboards.
    """

    def __init__(self, scoreboard: Scoreboard, fmt_string: str = "{}", default: int = 0):
        super().__init__(fmt_string, default)
        self.scoreboard = scoreboard

    def getValue(self) -> ScoreboardValue:
        return ScoreboardValue(Identifier(super().getValue()), self.scoreboard)

    def next(self) -> ScoreboardValue:
        val = self.getValue()
        super().next()
        return val

    def previous(self) -> ScoreboardValue:
        super().previous()
        return self.getValue()

    def clone(self) -> ScoreboardAddressCounter:
        a = ScoreboardAddressCounter(self.scoreboard, self.fmt_str, self.default)
        a.value = self.value
        return a


class StorageAddressCounter(AddressCounter):
    """
    A counter which formats the current value.
    Used to generate identifiers for data storages.
    """

    def __init__(self, base_path: DataPath, fmt_string: str = "{}", default: int = 0):
        super().__init__(fmt_string, default)
        self.base_path = base_path

    def getValue(self) -> DataPath:
        return self.base_path + super().getValue()

    def format(self, value: str) -> DataPath:
        return self.base_path + self.fmt_str.format(value)

    def next(self) -> DataPath:
        val = self.getValue()
        super().next()
        return val

    def previous(self) -> DataPath:
        super().previous()
        return self.getValue()

    def clone(self) -> StorageAddressCounter:
        a = StorageAddressCounter(self.base_path, self.fmt_str, self.default)
        a.value = self.value
        return a
