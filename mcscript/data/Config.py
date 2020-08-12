from __future__ import annotations

import configparser
from functools import cached_property
from os.path import exists

from mcscript import Logger
from mcscript.utils.resources import ResourceSpecifier


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
            "name": "mcscript",
            "utils": "mcscript_utils"
        }

        self.config["scores"] = {
            "return": ".ret",
            "block": ".block",
        }

        # maximum scoreboard name has 16 chars so `name` must contain 12 chars at most
        self.config["scoreboards"] = {
            "main": self["compiler"]["name"]
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
    #               shortcuts               #
    #########################################
    @cached_property
    def NAME(self):
        return self.get_compiler("name")

    @cached_property
    def UTILS(self):
        return self.get_compiler("utils")

    @cached_property
    def RETURN_SCORE(self):
        return self.get_score("return")

    @cached_property
    def BLOCK_SCORE(self):
        return self.get_score("block")

    @cached_property
    def storage_id(self) -> ResourceSpecifier:
        """ Returns the data storage id. Default is mcscript:main """
        from mcscript.utils.resources import ResourceSpecifier
        return ResourceSpecifier(self.NAME, self.get_storage("name"))

    def get_compiler(self, key) -> str:
        return self["compiler"][key]

    def get_score(self, key) -> str:
        return self["scores"][key]

    def get_scoreboard(self, key) -> str:
        return self["scoreboards"][key]

    def get_storage(self, key) -> str:
        return self["storage"][key]

    # Utility functions

    def resource_specifier_main(self, name: str) -> ResourceSpecifier:
        return ResourceSpecifier(self.NAME, name)

    def __getitem__(self, item):
        return self.config[item]
