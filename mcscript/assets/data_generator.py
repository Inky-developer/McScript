import json
import tempfile
from os.path import exists, join, split
from subprocess import run
from typing import Dict

from mcscript import Logger, __version__
from mcscript.assets import getVersionDir
from mcscript.assets.download import DownloadMinecraftServer, getLatestVersion


def makeData(version: str) -> str:
    """
    writes all important minecraft data to a file and returns the path
    Note that this wil crash if the version is below 1.14.
    """

    version = version or getLatestVersion()

    # first test if the file already exists
    directory = getVersionDir(version)
    file = join(directory, "data.json")
    if exists(file):
        with open(file) as f:
            try:
                data = json.load(f)
                if data.get("version", 0) != __version__.__asset_version__:
                    Logger.warn(f"File '{file}' uses old version format {data.get('version', 0)} "
                                f"(Required {__version__.__asset_version__})")
                else:
                    Logger.debug(f"Already got data for version {version}")
                    return file
            except json.JSONDecodeError:
                pass

    contents = getDataJson(version)
    contents["version"] = __version__.__asset_version__
    with open(file, "w+") as f:
        json.dump(contents, f)
    Logger.info(f"Create data file {file}")
    return file


def getDataJson(version: str) -> Dict:
    """ Creates a json file containing all important minecraft data"""

    def getRegistries(path: str) -> Dict:
        """ Returns a dict containing the registries for biomes and features"""
        file = join(path, "reports", "registries.json")
        with open(file) as f:
            data = json.load(f)
        return {
            "biomes"  : data["minecraft:biome"]["entries"],
            "features": data["minecraft:structure_feature"]["entries"]
        }

    def getBlocks(path: str) -> Dict:
        """ returns a dict containing all blocks and blockstates"""
        file = join(path, "reports", "blocks.json")
        with open(file) as f:
            data = json.load(f)
        return {
            "blocks": data
        }

    with tempfile.TemporaryDirectory() as tempdir:
        generated = runDataGenerator(version, tempdir)
        return {**getRegistries(generated), **getBlocks(generated)}


def runDataGenerator(version: str, fpath: str) -> str:
    """ Downloads the versions, runs the data generator and returns the full path to the generated data"""
    path, file = split(DownloadMinecraftServer(version, fpath))
    Logger.info("[Assets] generating minecraft data...")

    # test if java is installed
    process = run(["java", "-version"], cwd=path)
    print("Process java version result:", process.returncode)

    completedProcess = run(["java", "-cp", file, "net.minecraft.data.Main", "-all"], cwd=path)
    completedProcess.check_returncode()

    return join(path, "generated")


if __name__ == '__main__':
    print(makeData("20w16a"))
