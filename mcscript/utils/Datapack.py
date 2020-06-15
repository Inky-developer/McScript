from __future__ import annotations

import io
import re
from functools import cached_property, lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Union

from mcscript.data import getDictionaryResource
from mcscript.data.blockStorage.BlockTree import BlockTree
from mcscript.data.blockStorage.Generator import BlockFunctionGenerator, BlockTagGenerator, IdToBlockGenerator
from mcscript.data.commands import stringFormat
from mcscript.data.Config import Config
from mcscript.data.minecraftData import blocks
from mcscript.data.predicates.BiomePredicate import BiomePredicate
from mcscript.data.predicates.FeaturePredicate import FeaturePredicate
from mcscript.data.predicates.LightPredicate import LightPredicate
from mcscript.data.predicates.RandomPredicate import RandomPredicate
from mcscript.data.predicates.WeatherPredicate import WeatherPredicate
from mcscript.utils.FileStructure import FileStructure


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
            return self.fileStructure[file]
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
            with open(base.joinpath(self.getFileName(name, file)), "w", encoding="utf-8") as f:
                f.write(self.fileStructure[file].getvalue())

        for directory in self.subDirectories:
            self.subDirectories[directory].write(directory, base)

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
            "functions"   : FunctionDirectory,
            "loot_tables" : None,
            "predicates"  : None,
            "recipes"     : None,
            "structures"  : None,
            "tags"        : {
                "blocks"      : None,
                "entity_types": None,
                "fluids"      : None,
                "functions"   : None,
                "items"       : None,
            },
        })


class MinecraftNamespace(Namespace):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # whether the worldborder should be used get precise timings within a tick
        # Is set in the getTickTime Function and read in defaultCode.py
        self.hasSubTickClock = False

    def on_tags_functions(self, directory: Directory):
        data = getDictionaryResource("DefaultFiles.txt")

        # add tick and loadToScoreboard tags
        directory.addFile("tick.json").write(stringFormat(data["tag_tick"]))

        directory.addFile("load.json").write(stringFormat(data["tag_load"]))


class MainNamespace(Namespace):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_functions(self, directory):
        data = getDictionaryResource("DefaultFiles.txt")

        file = "load_lite" if not self.config.get_compiler("load_debug") else "load"
        # add loadToScoreboard function
        string = stringFormat(data[file])
        directory.addFile("load.mcfunction").write(string)


class HelperNamespace(Namespace):
    def __init__(self, config: Config):
        super().__init__(config)
        self.hasGetBlockFunction = False
        self.hasSetBlockFunction = False
        self.hasWeatherPredicate = False
        self.hasLightPredicate = False
        self.hasBiomePredicate = False
        self.hasFeaturePredicate = False
        self.hasRandomPredicate = False

    # cached blockTree for later
    @cached_property
    def blockTree(self):
        return BlockTree.fromList(blocks.getBlocks())

    def addGetBlockFunction(self):
        if self.hasGetBlockFunction:
            return
        self.hasGetBlockFunction = True
        BlockTagGenerator(self.blockTree).generate(self.getPath("tags/blocks").fileStructure)
        BlockFunctionGenerator(self.blockTree).generate(self.getPath("functions").fileStructure)

    def addSetBlockFunction(self):
        if self.hasSetBlockFunction:
            return
        self.hasSetBlockFunction = True
        IdToBlockGenerator().generate(self.getPath("functions").fileStructure, self.config.RETURN_SCORE,
                                      self.config.BLOCK_SCORE)

    @lru_cache()
    def addWeatherPredicate(self):
        if self.hasWeatherPredicate:
            return
        self.hasWeatherPredicate = True
        filestructure = self.getPath("predicates").fileStructure
        return WeatherPredicate().generate(filestructure)

    @lru_cache()
    def addLightPredicate(self):
        if self.hasLightPredicate:
            return
        self.hasLightPredicate = True
        filestructure = self.getPath("predicates").fileStructure
        return LightPredicate().generate(filestructure)

    @lru_cache()
    def addBiomePredicate(self):
        if self.hasBiomePredicate:
            return
        self.hasBiomePredicate = True
        filestructure = self.getPath("predicates").fileStructure
        return BiomePredicate().generate(filestructure)

    @lru_cache()
    def addFeaturePredicate(self):
        if self.hasFeaturePredicate:
            return
        self.hasFeaturePredicate = True
        filestructure = self.getPath("predicates").fileStructure
        return FeaturePredicate().generate(filestructure)

    @lru_cache()
    def addRandomPredicate(self):
        if self.hasRandomPredicate:
            return
        self.hasFeaturePredicate = True
        filestructure = self.getPath("predicates").fileStructure
        return RandomPredicate().generate(filestructure)


class Datapack(Directory):
    def __init__(self, config: Config):
        super().__init__(config, {
            "pack.mcmeta": None,
            "data"       : {
                "minecraft"                 : MinecraftNamespace,
                config.get_compiler("name") : MainNamespace,
                config.get_compiler("utils"): HelperNamespace
            },
        })

    def getMainDirectory(self) -> Directory:
        return self.getPathFromList(["data", self.config.NAME])

    def getUtilsDirectory(self) -> Directory:
        return self.getPathFromList(["data", self.config.UTILS])

    def on_pack_mcmeta(self, file):
        file.write(stringFormat(getDictionaryResource("DefaultFiles.txt")["mcmeta"]))
