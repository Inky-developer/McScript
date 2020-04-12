from typing import Dict

from mcscript import Logger


def getPrecompileInstructions(program: str) -> Dict[str, str]:
    """
    scrapes the document for comments with the format:

    ``#SET <KEY> = <VALUE>``

    These instructions will then be used to specify things like the output directory.
    Note that precompile instructions have precedence over cli parameters.

    Currently used instructions:
        -outpath       the output directory. if path does not exist, it will be created.
        -mcpath        mutually exclusive to outpath, defaults to %AppData%/.minecraft/saves
        -world         if mcpath if specified the world name to add this datapack to
        -name          The name of the datapack

    Args:
        program: the program string

    Returns:
        A Dictionary with the keys and values that were extracted

    """
    out = {}
    for line in program.split("\n"):
        if line.startswith("#"):
            line = line[1:].strip()
            if line.startswith("SET "):
                line = line[4:]
                try:
                    key, value = line.split("=", 1)
                except ValueError:
                    Logger.debug(f"[PreCompileInstructions] skipped '{line}': failed to parse")
                    continue
                key = key.strip()
                value = value.strip()
                out[key] = value
            # logger for slightly wrong statements
            elif line.startswith("SET"):
                maybe = f"SET {line[3:]}"
                Logger.debug(f"[PreCompileInstructions] skipped '{line}'. Maybe you meant '{maybe}'?")
            elif line.lower().startswith("set"):
                Logger.debug(f"[PreCompileInstructions] skipped '{line}'. Expected syntax: SET <key> = <value>")

    return out
