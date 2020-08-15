from importlib.resources import read_text


def getResource(name: str) -> str:
    text = read_text("mcscript.data.res", name)
    return text
