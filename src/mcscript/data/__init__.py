from functools import lru_cache
from importlib.resources import read_text
from typing import Dict

from src.mcscript.data.Config import Config
from src.mcscript.data.templates import DataReader


def getResource(name: str) -> str:
    text = read_text("src.mcscript.data.templates", name)
    return text


@lru_cache()
def getDictionaryResource(name: str) -> Dict[str, str]:
    text = getResource(name)
    return {k: v[0] if len(v) == 1 else v for k, v in DataReader().read(text).items()}


def getBlocks() -> str:
    if path := Config.currentConfig.get("block_list_path"):
        with open(path) as f:
            return f.read()
    return getResource("blockDump.txt")


def getItems() -> str:
    if path := Config.currentConfig.get("item_list_path"):
        with open(path) as f:
            return f.read()
    return getResource("itemDump.txt")


def getBiomes() -> str:
    if path := Config.currentConfig.get("biome_list_path"):
        with open(path) as f:
            return f.read()
    return getResource("biomeDump.json")


def getFeatures() -> str:
    if path := Config.currentConfig.get("feature_list_path"):
        with open(path) as f:
            return f.read()
    return getResource("FeatureDump.json")


__all__ = "getResource", "getDictionaryResource", "getBlocks", "getItems", "getBiomes", "getFeatures"
