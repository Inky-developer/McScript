from typing import List

from mcscript.data import defaultEnums, Config


def generate(config: Config) -> List:
    ret = []
    for enumName in defaultEnums.ENUMS:
        enum = defaultEnums.ENUMS[enumName]()
        values = [{"key": key, "value": enum.namespace[key].toString(), "type": enum.namespace[key].type().value} for
                  key in enum.namespace]
        ret.append({"name": enumName, "values": values})
    return ret
