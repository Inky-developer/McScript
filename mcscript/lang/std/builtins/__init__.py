from typing import List

from mcscript.lang.resource.MacroResource import MacroResource
from mcscript.lang.std.builtins.impl import EXPORTS


def include() -> List[MacroResource]:
    return EXPORTS
