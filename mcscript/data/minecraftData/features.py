from dataclasses import dataclass
from typing import List, Optional

from mcscript.assets import getCurrentData


@dataclass(frozen=True)
class Feature:
    id: str
    protocol_id: int
    index: int

    @property
    def name(self):
        return self.id.split(":")[-1]


FEATURES: List[Feature] = []
loaded = False


def assertLoaded():
    if not loaded:
        features = getCurrentData().getData("features")
        for index, key in enumerate(features):
            FEATURES.append(Feature(key, features[key]["protocol_id"], index))


def getFeatures() -> List[Feature]:
    assertLoaded()
    return FEATURES


def getWithProtocolId(protocol_id: int) -> Optional[Feature]:
    for feature in getFeatures():
        if feature.protocol_id == protocol_id:
            return feature
    return None
