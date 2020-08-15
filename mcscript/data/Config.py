from __future__ import annotations

import configparser
from functools import cached_property
from os.path import exists, join
from typing import Optional, TYPE_CHECKING

from mcscript import Logger
from mcscript.assets.DataManager import DataManager
from mcscript.utils.resources import ResourceSpecifier

if TYPE_CHECKING:
    from mcscript.utils.cmdHelper import MCWorld


class Config:
    currentConfig: Config = None

    def __init__(self, path: str = None):
        if Config.currentConfig:
            Config.currentConfig = self
            Logger.warning("[Config] currentConfig already exists!")
        Config.currentConfig = self
        self.path = path
        self.config = configparser.ConfigParser()

        self._input_file: Optional[str] = None
        self._world: Optional[MCWorld] = None
        self._output_dir: Optional[str] = None
        self._data_manager: DataManager = DataManager()

        self.config["main"] = {
            "release": "False",
            "minecraft_version": "",
            "name": "mcscript"
        }

        self.config["scores"] = {
            "format_string": ".exp_{block}_{index}"
        }

        # maximum scoreboard name has 16 chars so `name` must contain 12 chars at most
        self.config["scoreboards"] = {
            "main": self["main"]["name"]
        }

        self.config["storage"] = {
            "name": "main",
            "stack": "state.stack",
            "temp": "state.temp"
        }

        if path:
            if not exists(path):
                Logger.info("[Config] Write default config")
                with open(path, "w+") as f:
                    self.config.write(f)
            self.config.read(path)
            Logger.info("[Config] loaded from file")

        if not self.checkData():
            raise ValueError("Invalid values for config detected!")

    def checkData(self):
        """ Checks that all data are in an allowed range """
        return (
            all(len(self.get_scoreboard(i)) <= 16 for i in ("main",))
        )

    #########################################
    #             Main variables            #
    #########################################
    @property
    def project_name(self) -> str:
        return self.get_main("name")

    @project_name.setter
    def project_name(self, value: str):
        self["main"]["name"] = value
        self["scoreboards"]["main"] = value

    @property
    def is_release(self) -> bool:
        return self.config.getboolean("main", "release")

    @is_release.setter
    def is_release(self, value: bool):
        self["main"]["release"] = str(value)

    @property
    def minecraft_version(self) -> Optional[str]:
        return self.get_main("minecraft_version") or None

    @minecraft_version.setter
    def minecraft_version(self, value: str):
        self["main"]["minecraft_version"] = value
        self._data_manager = DataManager(self.minecraft_version)

    #########################################
    #                 I/O                   #
    #########################################
    @property
    def input_file(self) -> Optional[str]:
        return self._input_file

    @input_file.setter
    def input_file(self, value: str):
        self._input_file = value

    @property
    def world(self) -> Optional[MCWorld]:
        return self._world

    @world.setter
    def world(self, value: MCWorld):
        self._world = value
        self.minecraft_version = str(self.world.mcVersion["Name"])

    @property
    def output_dir(self) -> str:
        if self.world is not None and self._output_dir is None:
            return join(self.world.getDatapackPath(), self.project_name)
        elif self._world is None and self._output_dir is not None:
            return self._output_dir
        else:
            raise ValueError(
                f"Either a world {self.world} should be specified or a output directory {self._output_dir}")

    @output_dir.setter
    def output_dir(self, directory: str):
        self._output_dir = directory

    @property
    def data_manager(self) -> DataManager:
        return self._data_manager

    #########################################
    #               shortcuts               #
    #########################################
    @cached_property
    def storage_id(self) -> ResourceSpecifier:
        """ Returns the data storage id. Default is mcscript:main """
        from mcscript.utils.resources import ResourceSpecifier
        return ResourceSpecifier(self.project_name, self.get_storage("name"))

    def get_main(self, key) -> str:
        return self["main"][key]

    def get_score(self, key) -> str:
        return self["scores"][key]

    def get_scoreboard(self, key) -> str:
        return self["scoreboards"][key]

    def get_storage(self, key) -> str:
        return self["storage"][key]

    # Utility functions

    def resource_specifier_main(self, name: str) -> ResourceSpecifier:
        return ResourceSpecifier(self.project_name, name)

    def __getitem__(self, item):
        return self.config[item]
