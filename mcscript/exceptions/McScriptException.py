from __future__ import annotations

import inspect
import itertools
from typing import ClassVar, TYPE_CHECKING

from mcscript import Logger
from mcscript.exceptions.utils.sourceAnnotation import SourceAnnotation, SourceAnnotationList

if TYPE_CHECKING:
    from mcscript.compiler import CompileState

ERROR_TYPE_COUNTER = 0


class McScriptException(Exception):
    ERROR_TYPE: ClassVar[int] = -1

    def __init__(self, msg: str):
        Logger.error(f"Exception occurred: {self.__class__.__name__}")

        debug_exception = ["\n".join(f"\t* {i}" for i in msg.split("\n"))]
        super().__init__(msg)
        debug_exception += self.get_stack()
        debug_exception = "\n".join(debug_exception)
        Logger.debug(f"Exception message:\n{debug_exception}")

    def __init_subclass__(cls, **kwargs):
        global ERROR_TYPE_COUNTER
        cls.ERROR_TYPE = ERROR_TYPE_COUNTER
        ERROR_TYPE_COUNTER += 1
        return cls

    def get_stack(self):
        stack = inspect.stack()
        log = []

        # don't include last three stacks: this method, this init, init of subclass error
        for frame in itertools.islice(reversed(stack), len(stack) - 3):
            _, file, line, func, *_ = frame
            log.append(f"\t* {file}, line {line} in {func}")

        return log


class McScriptError(McScriptException):
    """ base McScript error"""

    def __init__(self, message, compileState: CompileState, *source_annotations: SourceAnnotation, showErr=True):
        tree = compileState.currentTree
        if tree is not None:
            header = f"McScript Exception [E{self.ERROR_TYPE}]\n" \
                     f"At line {tree.line} column {tree.column}\n"
            msg = SourceAnnotationList()
            if showErr:
                msg += SourceAnnotation.from_token(compileState.code, tree, message)
            else:
                msg += message

            # if custom annotations specified, include them and sort everything by line numbers
            if source_annotations:
                msg += SourceAnnotationList(*[i for i in source_annotations if i is not None])
                msg = msg.sorted()

            msg = header + str(msg)
        else:
            msg = message
        super().__init__(msg)
        self.tree = tree
