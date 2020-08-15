from os import makedirs
from os.path import join

import click

APP_NAME = "McScript"
ASSET_DIRECTORY = join(click.get_app_dir(APP_NAME, roaming=False), "assets")
makedirs(ASSET_DIRECTORY, exist_ok=True)

LOG_DIRECTORY = join(click.get_app_dir(APP_NAME, roaming=True), "logs")
makedirs(LOG_DIRECTORY, exist_ok=True)

VERSION_DIR = join(ASSET_DIRECTORY, "versions")


def getVersionDir(version: str) -> str:
    """ A dir for assets for the different minecraft versions """
    path = join(VERSION_DIR, version)
    makedirs(path, exist_ok=True)
    return path
