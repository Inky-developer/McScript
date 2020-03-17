from importlib.resources import read_text
from typing import Dict, List

from src.mcscript.data import DataReader


def loadScripts() -> Dict[str, List[str]]:
    content = read_text("test.Language", "TestScripts.txt")
    data = DataReader().read(content)
    return data
