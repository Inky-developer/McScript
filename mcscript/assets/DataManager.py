import json
from typing import Dict, Optional

from mcscript import Logger
from mcscript.assets.data_generator import makeData


class DataManager:
    def __init__(self, version: str = None):
        self.version = version
        self.data: Optional[Dict] = None

    def assertData(self):
        if self.data is None:
            file = makeData(self.version)
            with open(file, encoding="utf-8") as f:
                try:
                    self.data = json.load(f)
                except Exception as e:
                    Logger.info("[DataManager] could not parse json.\n" + f.read())
                    raise e

    def get_data(self, key: str = None) -> Dict:
        self.assertData()
        if not key:
            return self.data
        return self.data[key]
