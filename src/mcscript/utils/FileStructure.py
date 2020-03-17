from __future__ import annotations

import io
from collections import OrderedDict
from typing import List, Dict, Tuple


class FileStructure:
    def __init__(self):
        self.subFiles: Dict[str, io.StringIO] = OrderedDict()
        self.subDirectories: Dict[str, FileStructure] = OrderedDict()
        self.stack: List[io.StringIO] = []
        self.pois: Dict[str, Tuple[io.StringIO, str]] = {}

    def get(self):
        return self.stack[-1]

    def pushFile(self, name):
        self.stack.append(io.StringIO())
        self.subFiles[str(name)] = self.stack[-1]

    def popFile(self) -> io.StringIO:
        return self.stack.pop()

    def setPoi(self, function):
        self.pois[function.name()] = self.subFiles[next(reversed(self.subFiles))], function.blockName

    def addDirectory(self, name: str, directory: FileStructure):
        self.subDirectories[name] = directory

    def __str__(self):
        fileNames = []
        for i in self.subFiles:
            file = self.subFiles[i]
            pos = file.tell()
            file.seek(0)
            content = file.read()
            file.seek(pos)
            fileNames.append(f"{i}:\n{content}\n-----------------\n")
        return "\n".join(fileNames)
