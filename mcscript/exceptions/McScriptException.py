import inspect
import itertools

from mcscript import Logger


class McScriptException(Exception):
    def __init__(self, msg: str):
        Logger.error(f"Exception occurred: {self.__class__.__name__}")

        debug_exception = ["\n".join(f"\t* {i}" for i in msg.split("\n"))]
        super().__init__(msg)
        debug_exception += self.get_stack()
        debug_exception = "\n".join(debug_exception)
        Logger.debug(f"Exception message:\n{debug_exception}")

    def get_stack(self):
        stack = inspect.stack()
        log = []

        # don't include last three stacks: this method, this init, init of subclass error
        for frame in itertools.islice(reversed(stack), len(stack) - 3):
            _, file, line, func, *_ = frame
            log.append(f"\t* {file}, line {line} in {func}")

        return log
