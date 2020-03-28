import re
from typing import Dict, List

from src.mcscript.data import Config
from src.mcscript.data.builtins.builtins import BuiltinFunction

"""
used to generated autodoc for the vscode extension. 
"""

pParameter = re.compile(r"\W*parameter\W*=>(\W*\[(Optional|List)\])?\W*(\w+)((:)\W*(\w+))?\W*(.*)")


def generate(config: Config) -> List[Dict]:
    ret = []
    for builtinFunction in BuiltinFunction.functions:
        name = builtinFunction.name()
        returnType = builtinFunction.returnType().value
        doc = str(builtinFunction.__doc__)
        doc, parameters = parseDoc(doc)
        ret.append(dict(name=name, returnType=returnType, parameters=parameters, doc=doc))
    return ret


def parseDoc(doc: str):
    nDoc = []
    ret = []
    for line in doc.split("\n"):
        if match := pParameter.match(line):
            _, mod, pName, _, _, pType, doc = match.groups()
            mod = mod or "Default"
            ret.append({"name": pName, "type": pType, "doc": doc, "modifier": mod})
        else:
            line = line.strip()
            if line:
                nDoc.append(line)
    return "\n".join(nDoc), ret
