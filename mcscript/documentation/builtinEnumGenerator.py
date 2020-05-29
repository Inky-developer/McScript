from mcscript.data import Config, defaultEnums


def generate(_: Config) -> list:
    """
    Generates a list which contains all default enums.

    Format:
        [
            {
                "name": enumName,
                "values": [
                    "key": key,
                    "value": value,
                    "type": type
                ]
            }
        ]

    Args:
        _: The config, unused here

    Returns:
        a list containing all default enums
    """
    ret = []
    for enumName in defaultEnums.ENUMS:
        enum = defaultEnums.ENUMS[enumName]()
        values = [{"key": key, "value": enum.context[key].toString(), "type": enum.context[key].type().value} for
                  key in enum.context]
        ret.append({"name": enumName, "values": values})
    return ret
