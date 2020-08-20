import re
from contextlib import contextmanager
from os import makedirs
from pathlib import Path
from subprocess import Popen
from time import sleep
from typing import Dict, IO, ContextManager

import pytest
from mcrcon import MCRcon

from mcscript.assets.download import get_latest_version, download_minecraft_server
from mcscript.data.Config import Config


class MinecraftServer:
    class SimplePropertiesParser:
        PROPERTIES_PATTERN = re.compile(r"([\w\-.]+) *= *([^\n]*)")

        def __init__(self):
            self.data: Dict[str, str] = {}

        def read(self, file):
            with open(file) as f:
                self.read_text(f.read().strip())

        def read_text(self, text: str):
            for line in text.splitlines():
                if line.startswith("#"):
                    continue
                match = self.PROPERTIES_PATTERN.match(line)
                if match is not None:
                    key, value = match.groups()
                    self[key] = value

        def write(self, file: IO):
            for key, value in self.data.items():
                file.write(f"{key}={value}\n")

        def __setitem__(self, key: str, value: str):
            self.data[key] = value

        def __getitem__(self, item: str) -> str:
            return self.data[item]

    RCON_PORT = "25576"
    RCON_PASSWORD = "0000"

    def __init__(self, version=None):
        self.config = Config()
        self.config.minecraft_version = version or get_latest_version()

        self.server_dir = Path("server/")
        self.server_info_path = self.server_dir / "info.dat"
        if not self.server_info_path.exists():
            makedirs(self.server_info_path.parent, exist_ok=True)
            with open(self.server_info_path, "w+") as f:
                f.write("{0}\n".format(self.config.minecraft_version))
                self.server_path = Path(download_minecraft_server(self.config.minecraft_version, self.server_dir))
                f.write(str(self.server_path))
            self.init_server()
        else:
            with open(self.server_info_path) as f:
                if f.readline().strip() != self.config.minecraft_version:
                    self.server_path = download_minecraft_server(self.config.minecraft_version, self.server_dir)
                else:
                    self.server_path = Path(f.readline().strip())

    @contextmanager
    def run_server(self) -> ContextManager[MCRcon]:
        server_process = Popen(
            ["java", "-jar", self.server_path.name, "--nogui"],
            cwd=self.server_dir
        )
        # There must be a better way
        rcon = None
        for i in range(72):
            sleep(5)
            try:
                rcon = MCRcon("localhost", self.RCON_PASSWORD, int(self.RCON_PORT))

                # tries to create a connection
                with rcon:
                    pass
                break
            except ConnectionError:
                continue
        else:
            server_process.kill()
            pytest.fail("Could not connect to the minecraft server after 5 minutes")

        with rcon:
            try:
                yield rcon
            finally:
                rcon.command("stop")
                server_process.wait(30)

    def init_server(self):
        # first launch to create eula and properties
        Popen(["java", "-jar", self.server_path.name, "--initSettings"], cwd=self.server_dir).wait(300)

        with open(self.server_dir / "eula.txt", "r") as eula:
            contents = eula.read()
            contents = contents.replace("false", "true")

        with open(self.server_dir / "eula.txt", "w") as eula:
            eula.write(contents)

        parser = self.SimplePropertiesParser()
        parser.read(self.server_dir / "server.properties")

        parser["server-port"] = "25560"
        parser["rcon.port"] = self.RCON_PORT
        parser["rcon.password"] = self.RCON_PASSWORD
        parser["enable-rcon"] = "true"
        parser["motd"] = "McScript test server"

        with open(self.server_dir / "server.properties", "w") as f:
            parser.write(f)
