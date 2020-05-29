from __future__ import annotations

from mcscript.lang.resource.AddressResource import AddressResource
from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from mcscript.utils.Address import Address


class NbtAddress(Address):
    """
    Address for nbt values
    """

    def getValue(self) -> NbtAddressResource:
        return self._from(super().getValue())

    def next(self) -> NbtAddressResource:
        return self._from(super().next())

    def previous(self) -> NbtAddressResource:
        return self._from(super().previous())

    def with_name(self, name: str) -> NbtAddressResource:
        return NbtAddressResource(self.fmt_str.format(name))

    def clone(self) -> NbtAddress:
        address = NbtAddress(self.fmt_str, self.default)
        address.value = self.value
        return address

    def _from(self, value: AddressResource) -> NbtAddressResource:
        return NbtAddressResource(value.embed())
