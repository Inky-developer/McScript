from __future__ import annotations

import io
import re
from functools import cached_property
from pathlib import Path
from typing import Dict, Union, List, Optional

from src.mcscript.data import getDictionaryResource
from src.mcscript.data.Commands import stringFormat
from src.mcscript.data.Config import Config
from src.mcscript.data.blockStorage.BlockTree import BlockTree
from src.mcscript.data.blockStorage.Generator import BlockTagGenerator, BlockFunctionGenerator, IdToBlockGenerator
from src.mcscript.data.blocks import Blocks
from src.mcscript.utils.FileStructure import FileStructure


class Directory:
    """ Contains files (A FileStructure class) and sub-directories"""

    def __init__(self, config: Config, structure=None, listeners=None):
        self.config = config
        self.fileStructure: FileStructure = FileStructure()
        self.subDirectories: Dict[str, Directory] = {}
        self.listeners = listeners or {}

        if structure:
            self._createStructure(structure, self.listeners)

    def addFile(self, name: str) -> io.StringIO:
        self.fileStructure.pushFile(name)
        return self.fileStructure.get()

    def addDirectory(self, name: str, *args, **kwargs) -> Directory:
        directory = Directory(self.config, *args, **kwargs)
        self.subDirectories[name] = directory
        return directory

    def getPath(self, path: str) -> Union[io.StringIO, Directory]:
        """
        resolves a path and returns either a directory or a file.
        path format:
            - foo/bar/baz
            - path/to/a/file.txt
        """
        pathList = re.split(r"[/\\]", path)
        file = None

        if len(pathList) > 1 and not pathList[-1]:
            pathList.pop()
        if "." in pathList[-1]:
            file = pathList.pop()
        return self.getPathFromList(pathList, file)

    def getPathFromList(self, folders: List[str], file: Optional[str] = None) -> Union[io.StringIO, Directory]:
        if folders:
            folder = folders.pop(0)
            try:
                directory = self.subDirectories[folder]
            except KeyError:
                raise ValueError(f"Non-existing path including {folder}")
            return directory.getPathFromList(folders, file)

        if not file:
            return self

        try:
            return self.fileStructure.subFiles[file]
        except KeyError:
            raise AttributeError(f"Non-existing file {file}")

    def write(self, name: str, path: Path):
        base = path.joinpath(name)
        # this causes just trouble
        # if base.exists():
        #     shutil.rmtree(base)
        base.mkdir(exist_ok=True)
        for file in self.fileStructure.subFiles:
            # noinspection PyTypeChecker
            with open(base.joinpath(self.getFileName(name, file)), "w") as f:
                f.write(self.fileStructure.subFiles[file].getvalue())

        for directory in self.subDirectories:
            self.subDirectories[directory].write(directory, base)

    def getFileName(self, dirName, rawName: str) -> str:
        return rawName

    def _createStructure(self, structure: Dict, listeners):
        """
        Creates empty templates given by this dict.
        Format:
            filename: string -> None: creates an empty Directory or a file if the name contains a dot (.).
            filename: string -> Dictionary: create a Dictionary pregenerated with the given Dictionary.
            filename: string -> callable: creates a custom type of object.
        Calls the method on_<filename>(file_or_dictionary) when the file or dictionary was created.
        """
        for filename in structure:
            value = structure[filename]
            function = getattr(self, f"on_{filename.replace('.', '_')}", None)
            file = None
            if value is None:
                if "." in filename:
                    file = self.addFile(filename)
                else:
                    file = self.addDirectory(filename)
            elif isinstance(value, dict):
                listeners = {key: getattr(self, f"on_child_{key.replace('.', '_')}") for key in value.keys() if
                             getattr(self, f"on_child_{key.replace('.', '_')}", None)}
                listeners.update(self.listeners)
                file = self.addDirectory(filename, value, listeners=listeners)
            else:
                if not callable(value):
                    raise AttributeError("Custom object must be callable")
                file = value(config=self.config)
                self.subDirectories[filename] = file
            if file:
                if function:
                    function(file)
                if filename in listeners:
                    listeners[filename](file)


class FunctionDirectory(Directory):
    def getFileName(self, _, rawName: str) -> str:
        if rawName.split(".")[-1].lower() == "mcfunction":
            return rawName
        return rawName + ".mcfunction"


class Namespace(Directory):
    def __init__(self, config: Config):
        super().__init__(config, {
            "advancements": None,
            "functions": FunctionDirectory,
            "loot_tables": None,
            "predicates": None,
            "recipes": None,
            "structures": None,
            "tags": {
                "blocks": None,
                "entity_types": None,
                "fluids": None,
                "functions": None,
                "items": None,
            },
        })


class MinecraftNamespace(Namespace):
    def on_child_functions(self, directory: Directory):
        data = getDictionaryResource("DefaultFiles.txt")

        # add tick and loadToScoreboard tags
        directory.addFile("tick.json").write(stringFormat(data["tag_tick"]))

        directory.addFile("loadToScoreboard.json").write(stringFormat(data["tag_load"]))


class MainNamespace(Namespace):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_functions(self, directory):
        data = getDictionaryResource("DefaultFiles.txt")

        file = "load_lite" if not self.config.get("load_debug") else "load"
        # add loadToScoreboard function
        directory.addFile("load.mcfunction").write(stringFormat(data[file]))


class HelperNamespace(Namespace):
    def __init__(self, config: Config):
        super().__init__(config)

    # cached blockTree for later
    @cached_property
    def blockTree(self):
        return BlockTree.fromList(Blocks.getBlocks())

    def addGetBlockFunction(self):
        BlockTagGenerator(self.blockTree).generate(self.getPath("tags/blocks").fileStructure)
        BlockFunctionGenerator(self.blockTree).generate(self.getPath("functions").fileStructure)

    def addSetBlockFunction(self):
        IdToBlockGenerator().generate(self.getPath("functions").fileStructure, self.config.RETURN_SCORE,
                                      self.config.BLOCK_SCORE)


class Datapack(Directory):
    def __init__(self, config: Config):
        super().__init__(config, {
            "pack.mcmeta": None,
            "data": {
                "minecraft": MinecraftNamespace,
                config.get("name"): MainNamespace,
                config.get("utils"): HelperNamespace
            },
        })

    def getMainDirectory(self) -> Directory:
        return self.getPathFromList(["data", self.config.NAME])

    def getUtilsDirectory(self) -> Directory:
        return self.getPathFromList(["data", self.config.UTILS])

    def on_pack_mcmeta(self, file):
        file.write(stringFormat(getDictionaryResource("DefaultFiles.txt")["mcmeta"]))
