from mcscript.assets.DataManager import DataManager

_CurrentData = DataManager()


def getCurrentData():
    return _CurrentData


def setCurrentData(version: str):
    global _CurrentData
    _CurrentData = DataManager(version)
