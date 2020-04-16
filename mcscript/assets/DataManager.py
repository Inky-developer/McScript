import json
from typing import Dict, Optional

from mcscript.assets.data_generator import makeData


class DataManager:
    def __init__(self, version: str = None):
        self.version = version
        self.data: Optional[Dict] = None

    def assertData(self):
        if self.data is None:
            file = makeData(self.version)
            with open(file) as f:
                self.data = json.load(f)

    def getData(self, key: str = None) -> Dict:
        self.assertData()
        if not key:
            return self.data
        return self.data[key]
