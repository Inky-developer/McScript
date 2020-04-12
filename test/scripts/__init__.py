from importlib.resources import read_text


def getScript(name: str) -> str:
    text = read_text("test.scripts", name + ".mcscript")
    return text
