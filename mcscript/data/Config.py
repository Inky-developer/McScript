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

        self.config["data"] = {
            "block_list_path": "",
            "item_list_path": "",
            "biome_list_path": "",
            "feature_list_path": ""
        }
        self.config["compiler"] = {
            "load_debug": False,
            "name": "mcscript",
            "utils": "mcscript_utils",
            "return_score": ".ret",
            "block_score": ".block"
        }

        if path:
            if not exists(path):
                Logger.info("[Config] Write default config")
                with open(path, "w+") as f:
                    self.config.write(f)
            self.config.read(path)
            Logger.info("[Config] loaded from file")

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
        return AddressResource(self.get_compiler("return_score"), True)

    @property
    @lru_cache()
    def BLOCK_SCORE(self):
        from mcscript.lang.resource.AddressResource import AddressResource
        return AddressResource(self.get_compiler("block_score"), True)

    def get_compiler(self, key) -> str:
        return self["compiler"][key]

    def get_data(self, key) -> str:
        return self["data"][key]

    def __getitem__(self, item):
        return self.config[item]
