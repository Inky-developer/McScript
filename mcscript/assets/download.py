import json
from os.path import join
from typing import Dict
from urllib.request import urlopen

import certifi
import click

from mcscript import Logger
from mcscript.utils.utils import run_function_once

VERSION_MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"


@run_function_once
def downloadVersionManifest() -> Dict:
    """
    Downloads the minecraft version manifest and returns it parsed as a dictionary

    Format:
        {
            "latest": {
                "release": str
                "snapshot": str
            },
            "versions": [
                {
                    "id": str,
                    "type": str,
                    "url": str,
                    "time": str,
                    "releaseTime": str
                }
            ]
        }

    Returns:
        The version manifest
    """
    Logger.info("[Assets] Fetching version manifest...")
    request = _get(VERSION_MANIFEST_URL)
    manifest = json.load(request)
    Logger.info("[Assets] Successfully fetched version manifest")
    Logger.debug(manifest)
    return manifest


def get_latest_version() -> str:
    return downloadVersionManifest()["latest"]["release"]


def getVersionUrl(version_id: str) -> str:
    """
    Downloads the version manifest returns the version url.

    Args:
        version_id: The version in the format "1.15.2" or "20w16a"

    Returns:
        The url for the version json
    """

    manifest = downloadVersionManifest()
    if not version_id:
        version_id = manifest["latest"]["release"]

    for version in manifest["versions"]:
        if version["id"] == version_id:
            return version["url"]

    raise ValueError(f"Could not find version '{version_id}'")


def download_minecraft_server(version_id: str, target: str) -> str:
    """
    Downloads the minecraft server for version `version_id` and returns the full path.

    Args:
        version_id: the id for the version
        target: the target directory

    Returns:
        The full file path to `server.jar`

    """
    url = getVersionUrl(version_id)

    Logger.info(f"[Assets] Downloading minecraft server json at {url}")

    version = json.load(_get(url))

    Logger.info("[Assets] Downloaded version.json")
    Logger.debug(version)

    server_url = version["downloads"]["server"]["url"]
    Logger.info(f"[Assets] Starting to download server {version['id']}...")
    with _get(server_url) as server:
        download_size = server.length
        with click.progressbar(length=download_size, label="Downloading server jar") as bar:
            fpath = join(target, "server.jar")
            with open(fpath, "wb+") as f:
                while chunk := server.read(16384):
                    f.write(chunk)
                    bar.update(len(chunk))
        Logger.info(f"[Assets] Downloaded {download_size / 1000000:.2f} mb")
        Logger.info(f"[Assets] Created server.jar at {fpath}")

    return fpath


def _get(url: str):
    try:
        request = urlopen(url, cafile=certifi.where(), timeout=20)
    except Exception as e:
        raise ConnectionError(f"[Assets] Request 'GET {url}' failed") from e
    if request is None:
        raise ConnectionError(f"Could not download the version manifest file")
    if request.status != 200:
        raise ConnectionError(
            f"Could not download the version manifest file: Bad response <{request.status} {request.msg}>"
        )

    return request
