""""
A command line interface
"""
from __future__ import annotations

from os import getenv, listdir, makedirs, mkdir
from os.path import join, isdir, exists, isfile, dirname, abspath, normpath
from pathlib import Path
from typing import List, Optional

from nbt.nbt import NBTFile

# Default .minecraft path
from src.mcscript.utils.Datapack import Datapack

MCPATH = join(getenv("APPDATA"), ".minecraft", "saves")

# Any world that is below Version 1.15 can't be supported
MINIMUM_VERSION = 2225


def generateFiles(world: MCWorld, datapack: Datapack, name="McScript"):
    if not world.satisfiesVersion(MINIMUM_VERSION):
        print(f"#### Warning: World {world.levelName} is below the minimum supported version. ####")
    datapack.write(name, Path(world.getDatapackPath()))


def getWorlds(path=MCPATH) -> List[MCWorld]:
    return [world for world in
            (MCWorld(join(path, f)) for f in listdir(path) if isMcWorld(join(path, f)))
            if world.satisfiesVersion(MINIMUM_VERSION)]


def getWorld(name, path=MCPATH) -> Optional[MCWorld]:
    for world in getWorlds(path):
        if world.levelName == name:
            return world
    raise ValueError(f"Could not detect world '{name}' in '{abspath(normpath(path))}'")


def isMcWorld(folder):
    level = join(folder, "level.dat")
    return isdir(folder) and exists(level) and isfile(level)


def _make(path):
    try:
        makedirs(path)
    except FileExistsError:
        pass


class MCWorld:
    def __init__(self, folderOrLevel):
        self.path = folderOrLevel
        if isdir(folderOrLevel):
            self.path = join(folderOrLevel, "level.dat")
        self.folder = dirname(self.path)

        try:
            self.level = NBTFile(self.path)
        except:
            raise ValueError(f"failed to open {self.path}")

        self.levelData = self.level[0]

        self.levelName = self.levelData["LevelName"].value
        self.mcVersion = self.levelData["Version"]

    def getDatapackPath(self):
        path = join(self.folder, "datapacks")
        if not isdir(path):
            mkdir(path)
        return path

    def satisfiesVersion(self, version: int):
        return self.mcVersion["Id"].value >= version

    def __eq__(self, other):
        return other and isinstance(other, MCWorld) and other.path == self.path

    def __hash__(self):
        return hash(self.path)

    def __repr__(self):
        return f"MCWorld({self.levelName})"


def DebugWrite(datapack: Datapack):
    generateFiles(getWorld("McScript", path="C:\\Users\\david\\AppData\\Roaming\\.minecraft\\saves"), datapack)
