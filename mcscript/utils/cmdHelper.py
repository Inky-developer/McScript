""""
Utilities for the command line interface.
"""
from __future__ import annotations

import sys
from os import getenv, listdir, mkdir
from os.path import abspath, dirname, exists, expanduser, isdir, isfile, join, normpath
from pathlib import Path
from typing import Iterator, Optional

from nbt.nbt import NBTFile

# Default .minecraft path
from mcscript import Logger
from mcscript.utils.Datapack import Datapack

# try to determine the default minecraft path
# resource: https://minecraft.gamepedia.com/.minecraft
if sys.platform.startswith("win"):
    MCPATH = join(getenv("APPDATA"), ".minecraft", "saves")
elif sys.platform.startswith("darwin"):
    MCPATH = join(expanduser("~"), "Library", "Application Support", "minecraft")
else:  # try to load the linux path
    MCPATH = join(expanduser("~"), ".minecraft")

# Any world that is below Version 1.15 can't be supported
MINIMUM_VERSION = 2225


def generateFiles(world: MCWorld, datapack: Datapack, name="McScript"):
    """
    Saves the datapack for `world`.

    Parameters:
        world: the minecraft world
        datapack: the 'Datapack' object
        name: the name of the datapack, default "McScript"
    """
    if not world.satisfiesVersion(MINIMUM_VERSION):
        Logger.Error(f"[WriteFiles] #### Warning: World {world.levelName} is below the minimum supported version. ####")
    datapack.write(name, Path(world.getDatapackPath()))


def getWorlds(path=MCPATH) -> Iterator[MCWorld]:
    """
    Returns all worlds in `path`

    Args:
        path: the path

    Returns:
        A List of MCWorld objects
    """
    return (world for world in
            (MCWorld(join(path, f)) for f in listdir(path) if isMcWorld(join(path, f)))
            if world.satisfiesVersion(MINIMUM_VERSION))


def getWorld(name, path=MCPATH) -> Optional[MCWorld]:
    """
    Returns a world that is located in `path` and named `name`

    Args:
        name: The name of the world. Not the folder name
        path: the path of the directory that contains this world

    Returns:
        a `MCWorld` instance if found or `None`
    """
    for world in getWorlds(path):
        if world.levelName == name:
            return world
    raise ValueError(f"Could not detect world '{name}' in '{abspath(normpath(path))}'")


def isMcWorld(folder):
    level = join(folder, "level.dat")
    return isdir(folder) and exists(level) and isfile(level)


class MCWorld:
    """
    A simple object to represent a single minecraft world.
    """

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


currentWorld: Optional[MCWorld] = None


def setCurrentWorld(world: MCWorld):
    global currentWorld
    currentWorld = world


def getCurrentWorld() -> MCWorld:
    return currentWorld
