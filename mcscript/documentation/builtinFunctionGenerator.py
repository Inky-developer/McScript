from typing import Dict, List

from mcscript.data import Config
from mcscript.lang.builtins.builtins import BuiltinFunction


def generate(_: Config) -> List[Dict]:
    """
    Generates a list of all builtin functions.

    Format:
        [
            {
                name: str,
                returnType: str,
                parameters: [
                    {
                        name: str,
                        type: str,
                        static: bool,
                        count: int (0=once,1=arbitrary,2=one_or_more),
                        default: {
                            hasDefault: bool,
                            default: str,
                            type: str
                        },
                        documentation: str
                    }
                ],
                inline: bool,
                signature: str,
                documentation: str
            }
        ]

    Args:
        _: the config, here unused

    Returns:
        The described list
    """
    return [dict(
        name=builtinFunction.name(),
        returnType=builtinFunction.getFunctionSignature.returnType.value,
        parameters=[
            dict(
                name=parameter.name,
                type=parameter.type.value.type().value,
                static=parameter.accepts == parameter.ResourceMode.STATIC,
                count=parameter.count.value,
                default=dict(
                    hasDefault=parameter.defaultValue is not None,
                    default=str(parameter.defaultValue) if parameter.defaultValue else None,
                    type=parameter.defaultValue.type().value if parameter.defaultValue else None
                ),
                documentation=parameter.documentation
            ) for parameter in builtinFunction.getFunctionSignature.parameters],
        inline=builtinFunction.getFunctionSignature.inline,
        signature=builtinFunction.getFunctionSignature.signature_string(),
        documentation=builtinFunction.getFunctionSignature.documentation
    ) for builtinFunction in BuiltinFunction.functions]
