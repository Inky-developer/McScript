from os import getcwd, makedirs
from os.path import join

import appdirs

try:
    # who uses vista?
    ASSET_DIRECTORY = appdirs.site_data_dir("McScript", "inky")
    makedirs(ASSET_DIRECTORY, exist_ok=True)
except PermissionError:
    # if something goes for some reason wrong, use the cwd as a fallback dir
    ASSET_DIRECTORY = join(getcwd(), "assets")
    makedirs(ASSET_DIRECTORY, exist_ok=True)
VERSION_DIR = "versions"


def getVersionDir(version: str) -> str:
    """ A dir for assets for the different minecraft versions """
    path = join(ASSET_DIRECTORY, VERSION_DIR, version)
    makedirs(path, exist_ok=True)
    return path


def getLogDir() -> str:
    path = join(ASSET_DIRECTORY, "Logs")
    makedirs(path, exist_ok=True)
    return path
