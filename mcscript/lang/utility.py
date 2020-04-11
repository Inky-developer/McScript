from __future__ import annotations

from mcscript.lang.resource.base.ResourceBase import Resource


def compareTypes(a: Resource, b: Resource) -> bool:
    """ compares two resources. """
    from mcscript.lang.resource.StructObjectResource import StructObjectResource
    from mcscript.lang.resource.StructResource import StructResource

    if isinstance(a, StructObjectResource):
        return isinstance(b, StructResource) and a.struct == b
    return a.type() == b.type() or b == Resource
