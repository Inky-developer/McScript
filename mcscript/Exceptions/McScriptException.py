from mcscript import Logger


class McScriptException(Exception):
    def __init__(self, msg: str):
        Logger.error(f"Exception occurred: {self.__class__.__name__}")

        debug_exception = "\n".join(f"\t* {i}" for i in msg.split("\n"))
        Logger.debug(f"Exception message:\n{debug_exception}")
        super().__init__(msg)
