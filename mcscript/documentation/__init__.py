import json

from mcscript.data import Config
from mcscript.documentation import builtinEnumGenerator, builtinFunctionGenerator


def generate_json(config: Config) -> str:
    """
    Generates a json file containing information about all default enums and builtin functions.

    Format:
        {
            "enums": {...},
            "builtins": {...}
        }

    Returns:
        a valid json string
    """
    dict_enums = builtinEnumGenerator.generate(config)
    dict_builtins = builtinFunctionGenerator.generate(config)

    return json.dumps({
        "enums"   : dict_enums,
        "builtins": dict_builtins
    }, sort_keys=True, indent=4)
