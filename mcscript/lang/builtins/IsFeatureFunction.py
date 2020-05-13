from __future__ import annotations

from typing import Dict, TYPE_CHECKING

from mcscript.data.commands import Command, ExecuteCommand, multiple_commands
from mcscript.data.minecraftData import features
from mcscript.data.minecraftData.features import Feature
from mcscript.exceptions.compileExceptions import McScriptArgumentsError
from mcscript.lang.builtins.builtins import CachedFunction
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class IsFeatureFunction(CachedFunction):
    """
    parameter => [Static] feature: Number the feature id
    returns whether the current entity is inside the bounding box of the specified feature.
    Example:
        "isFeature(features.village)"
        -> 1 or 0
    """

    def name(self) -> str:
        return "isFeature"

    def returnType(self) -> ResourceType:
        return ResourceType.BOOLEAN

    # noinspection PyTypeChecker
    def generate(self, compileState: CompileState, *parameters: Resource) -> str:
        parameter, = parameters
        feature = features.getWithProtocolId(int(parameter))
        if not feature:
            raise McScriptArgumentsError(f"Could not find feature with protocol id {parameter}.", compileState)

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
