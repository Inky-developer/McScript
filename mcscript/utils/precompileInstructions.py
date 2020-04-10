from typing import Dict


def getPrecompileInstructions(program: str) -> Dict[str, str]:
    out = {}
    for line in program.split("\n"):
        if line.startswith("#"):
            line = line[1:].strip()
            if line.startswith("SET "):
                line = line[4:]
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                out[key] = value
    return out
