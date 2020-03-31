from __future__ import annotations

from typing import TYPE_CHECKING, Dict

from src.mcscript.Exceptions import McScriptArgumentsError
from src.mcscript.data.Commands import Command, ExecuteCommand, multiple_commands
from src.mcscript.data.minecraftData import features
from src.mcscript.data.minecraftData.features import Feature
from src.mcscript.lang.builtins.builtins import CachedFunction
from src.mcscript.lang.resource.base.ResourceBase import Resource
from src.mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from src.mcscript import CompileState


class IsFeatureFunction(CachedFunction):
    """
    parameter => feature: Number the feature id
    returns whether the current entity is inside the bounding box of the specified feature.
    Example:
        "isFeature(features.village)"
        -> 1 or 0
    """

    def name(self) -> str:
        return "isFeature"

    def returnType(self) -> ResourceType:
        return ResourceType.BOOLEAN

    def generate(self, compileState: CompileState, *parameters: Resource) -> str:
        if len(parameters) != 1:
            raise McScriptArgumentsError("Function getBiome expected exactly one argument.")
        try:
            parameter = parameters[0].toNumber()
        except TypeError:
            raise McScriptArgumentsError("The argument <feature> could not be converted to a number.")

        feature = features.getWithProtocolId(parameter)
        if not feature:
            raise McScriptArgumentsError(f"Could not find feature with protocol id {parameter}.")

        return multiple_commands(
            Command.SET_VALUE(
                stack=compileState.config.RETURN_SCORE,
                value=0
            ),
            Command.EXECUTE(
                sub=ExecuteCommand.IF_PREDICATE(
                    predicate=self.predicates[feature]
                ),
                command=Command.SET_VALUE(
                    stack=compileState.config.RETURN_SCORE,
                    value=1
                )
            )
        )

    def include(self, compileState: CompileState):
        self.predicates: Dict[Feature, str] = compileState.datapack.getUtilsDirectory().addFeaturePredicate()
