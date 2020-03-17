from dataclasses import dataclass

from src.mcscript.lang.Resource import ResourceBase


@dataclass
class Variable:
    value: ResourceBase
    isConstant: bool
