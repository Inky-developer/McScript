from dataclasses import dataclass, field
from typing import List, Optional

from lark import Tree


@dataclass()
class ResourceMeta:
    """
    Holds information about the history of resources
    """
    first_declared: Optional[Tree] = None
    value_changes: List[Tree] = field(default_factory=list)
