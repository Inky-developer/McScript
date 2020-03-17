from __future__ import annotations

from src.mcscript.lang.Resource.AddressResource import AddressResource


class Address:
    def __init__(self, fmt_string: str = "{}", default: int = 0):
        self.fmt_str = fmt_string
        self.value = self.default = default

    def getValue(self) -> AddressResource:
        return AddressResource(self.fmt_str.format(self.value), True)

    def next(self) -> AddressResource:
        val = self.getValue()
        self.value += 1
        return val

    def previous(self) -> AddressResource:
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

    def clone(self) -> Address:
        a = Address(self.fmt_str, self.default)
        a.value = self.value
        return a
