from __future__ import annotations

import io
from collections import OrderedDict
from typing import List, Dict, Tuple


class FileStructure:
    def __init__(self):
        self._subFiles: Dict[str, io.StringIO] = OrderedDict()
        self._stack: List[io.StringIO] = []
        self.pois: Dict[str, Tuple[io.StringIO, str]] = {}

    def get(self):
        return self._stack[-1]

    def pushFile(self, name):
        self._stack.append(io.StringIO())
        self._subFiles[str(name)] = self._stack[-1]

    def popFile(self) -> io.StringIO:
        return self._stack.pop()

    def setPoi(self, function):
        self.pois[function.name()] = self._stack[-1], function.blockName

    # very inefficient but only used for debugging
    def __str__(self):
        fileNames = []
        for i in self._subFiles:
            file = self._subFiles[i]
            pos = file.tell()
            file.seek(0)
            content = file.read()
            file.seek(pos)
            fileNames.append(f"{i}:\n{content}\n-----------------\n")
        return "\n".join(fileNames)
