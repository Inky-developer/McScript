from src.mcscript.lang.resource.StructObjectResource import StructObjectResource
from src.mcscript.lang.resource.StructResource import StructResource
from src.mcscript.lang.resource.base.ResourceBase import Resource


def compareTypes(a: Resource, b: Resource) -> bool:
    """ compares two resources. """
    if isinstance(a, StructObjectResource):
        return isinstance(b, StructResource) and a.struct == b
    return a.type() == b.type()
