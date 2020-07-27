from typing import Type
from mcscript.ir.backends.mc_datapack_backend.McDatapackBackend import McDatapackBackend

BACKENDS = [McDatapackBackend]

def get_default_backend() -> Type[McDatapackBackend]:
    return McDatapackBackend