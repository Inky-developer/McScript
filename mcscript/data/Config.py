from __future__ import annotations

import configparser
from functools import lru_cache
from os.path import exists
from typing import TYPE_CHECKING

from mcscript import Logger

if TYPE_CHECKING:
    from mcscript.lang.resource.AddressResource import AddressResource


class Config:
    currentConfig: Config = None

    def __init__(self, path: str = None):
        if Config.currentConfig:
            Config.currentConfig = self
            Logger.warning("[Config] currentConfig already exists!")
        Config.currentConfig = self
        self.path = path
        self.config = configparser.ConfigParser()

        self.config["compiler"] = {
            "load_debug": False,
            "name"      : "mcscript",
            "utils"     : "mcscript_utils"
        }

        self.config["scores"] = {
            "return"  : ".ret",
            "block"   : ".block",
        }

        # maximum scoreboard name has 16 chars so `name` must contain 12 chars at most
        # warning and Todo: scores.main is unused!
        self.config["scoreboards"] = {
            "main": self["compiler"]["name"]
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
            all(len(self.get_scoreboard(i)) <= 16 for i in ("main", "entities"))
        )

    #           legacy getters              #
    #########################################
    @property
    @lru_cache()
    def NAME(self):
        return self.get_compiler("name")

    @property
    @lru_cache()
    def UTILS(self):
        return self.get_compiler("utils")

    @property
    @lru_cache()
    def RETURN_SCORE(self):
        from mcscript.lang.resource.AddressResource import AddressResource
        return AddressResource(self.get_score("return"), True)

    @property
    @lru_cache()
    def BLOCK_SCORE(self):
        from mcscript.lang.resource.AddressResource import AddressResource
        return AddressResource(self.get_score("block"), True)

    def get_compiler(self, key) -> str:
        return self["compiler"][key]

    def get_score(self, key) -> str:
        return self["scores"][key]

    def get_scoreboard(self, key) -> str:
        return self["scoreboards"][key]

    def __getitem__(self, item):
        return self.config[item]
