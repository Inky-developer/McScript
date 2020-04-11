from importlib.resources import read_text


def getScript(name: str) -> str:
    text = read_text("tests.scripts", name + ".mcscript")
    return text
