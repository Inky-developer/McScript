from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Dict, List, Optional, Union

from mcscript.backends.mc_datapack_backend import get_resource
from mcscript.data.Config import Config
from mcscript.utils.Files import Files


class Directory:
    """ Contains files (A `Files` class) and sub-directories"""

    def __init__(self, config: Config, structure=None, listeners=None):
        self.config = config
        self.files: Files = Files()
        self.subDirectories: Dict[str, Directory] = {}
        self.listeners = listeners or {}

        if structure:
            self._createStructure(structure, self.listeners)

    def addFile(self, name: str) -> io.StringIO:
        return self.files.push(name)

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
            return self.files[file]
        except KeyError:
            raise AttributeError(f"Non-existing file {file}")

    def write(self, path: Path):
        # this causes just trouble
        # if base.exists():
        #     shutil.rmtree(base)
        path.mkdir(exist_ok=True)
        for file_name in self.files:
            # noinspection PyTypeChecker
            with open(path.joinpath(self.getFileName(path, file_name)), "w", encoding="utf-8") as f:
                f.write(self.files[file_name].getvalue())

        for directory in self.subDirectories:
            self.subDirectories[directory].write(path.joinpath(directory))

    def getFileName(self, dirName, rawName: str) -> str:
        return rawName

    def _createStructure(self, structure: Dict, listeners):
        """
        Creates empty templates given by this dict.

        Format:
            - filename: string -> None: creates an empty Directory or a file if the name contains a dot (.).
            - filename: string -> Dictionary: create a Dictionary pregenerated with the given Dictionary.
            - filename: string -> callable: creates a custom type of object.

        Calls the method on_<filename>(file_or_dictionary) when the file or dictionary was created.
        """
        for filename in structure:
            value = structure[filename]
            function = getattr(self, f"on_{filename.replace('.', '_')}", None)
            # noinspection PyUnusedLocal wtf?
            if value is None:
                if "." in filename:
                    file = self.addFile(filename)
                else:
                    file = self.addDirectory(filename)
            elif isinstance(value, dict):
                listeners = {key: getattr(self, f"on_{filename}_{key.replace('.', '_')}") for key in value.keys() if
                             hasattr(self, f"on_{filename}_{key.replace('.', '_')}")}
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
                    listeners.pop(filename)(file)


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


class Datapack(Directory):
    def __init__(self, config: Config):
        super().__init__(config, {
            "pack.mcmeta": None,
            "data": {
                "minecraft": Namespace,
                config.project_name: Namespace
            },
        })

    def get_minecraft_directory(self) -> Directory:
        return self.getPathFromList(["data", "minecraft"])

    def getMainDirectory(self) -> Directory:
        return self.getPathFromList(["data", self.config.project_name])

    def on_pack_mcmeta(self, file):
        file.write(get_resource("pack.mcmeta"))
