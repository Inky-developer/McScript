from os import makedirs
from os.path import join

import appdirs

# who uses vista?
ASSET_DIRECTORY = appdirs.site_data_dir("McScript", "inky")
makedirs(ASSET_DIRECTORY, exist_ok=True)

VERSION_DIR = "versions"


def getVersionDir(version: str):
    """ A dir for assets for the different minecraft versions """
    path = join(ASSET_DIRECTORY, VERSION_DIR, version)
    makedirs(path, exist_ok=True)
    return path


from mcscript.assets.DataManager import DataManager

_CurrentData = DataManager()


def getCurrentData():
    return _CurrentData


def setCurrentData(version: str):
    global _CurrentData
    _CurrentData = DataManager(version)
