from importlib.resources import read_text


def get_resource(name: str) -> str:
    text = read_text("mcscript.backends.mc_datapack_backend.res", name)
    return text
