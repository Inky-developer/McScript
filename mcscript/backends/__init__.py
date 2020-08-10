from typing import Type

from mcscript.backends.mc_datapack_backend import McDatapackBackend

BACKENDS = [McDatapackBackend]


def get_default_backend() -> Type[McDatapackBackend]:
    return McDatapackBackend
