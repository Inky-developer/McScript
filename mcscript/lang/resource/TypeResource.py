from mcscript.lang.Type import Type
from mcscript.lang.atomic_types import MetaType
from mcscript.lang.resource.base.ResourceBase import Resource


class TypeResource(Resource):
    """
    Holds a resource type
    """

    def type(self) -> Type:
        return MetaType

    def supports_scoreboard(self) -> bool:
        # Technically possible
        return False

    def supports_storage(self) -> bool:
        return False

    def __init__(self, static_value: Type):
        self.static_value = static_value
