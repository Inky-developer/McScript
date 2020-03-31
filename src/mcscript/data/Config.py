from __future__ import annotations

import ast
import configparser
import warnings
from functools import lru_cache
from os.path import exists
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src.mcscript.lang.resource.AddressResource import AddressResource


class Config:
    currentConfig: Config = None

    def __init__(self, fpath: str = None):
        if Config.currentConfig:
            warnings.warn("currentConfig already exists!")
        Config.currentConfig = self
        self.path = fpath
        self.config = configparser.ConfigParser({
            "name": "mcscript",
            "utils": "mcscript_utils",
            "load_debug": False,
            "block_list_path": "",
            "item_list_path": "",
            "biome_list_path": "",
            "feature_list_path": "",
            "addresses": {
                "return_score": ".ret",
                "block_score": ".block"
            }
        })
        if fpath:
            if not exists(fpath):
                self.config.write(open(fpath, "w+"))
            self.config.read(fpath)
        if "Configuration" not in self.config.sections():
            self.config.add_section("Configuration")
            if fpath:
                self.config.write(open(fpath, "w+"))

    #           legacy getters              #
    #########################################
    @property
    @lru_cache()
    def NAME(self):
        return self.get("name")

    @property
    @lru_cache()
    def UTILS(self):
        return self.get("utils")

    @property
    @lru_cache()
    def RETURN_SCORE(self):
        return self.get("return_score")

    @property
    @lru_cache()
    def BLOCK_SCORE(self):
        return self.get("block_score")

    #########################################

    def get(self, key: str) -> Any:
        if key in self.config["Configuration"]["addresses"]:
            return self._addressFormat(ast.literal_eval(self.config["Configuration"]["addresses"])[key])
        return self.config["Configuration"][key]

    def _addressFormat(self, name: str) -> AddressResource:
        from src.mcscript.lang.resource.AddressResource import AddressResource
        return AddressResource(name, True)

    def __setitem__(self, key, value):
        self.config["Configuration"][key] = value

    def __getitem__(self, item):
        return self.config["Configuration"][item]
