from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.resource.base.ResourceType import ResourceType


class TypeResource(Resource):
    """
    Holds a resource type
    """

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.TYPE

    def __init__(self, static_value: ResourceType):
        self.static_value = static_value
