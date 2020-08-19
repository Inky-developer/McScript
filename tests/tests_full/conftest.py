import pytest

from mcscript.utils.cmdHelper import MCWorld
from tests.tests_full.setup import MinecraftServer


@pytest.fixture(scope="session")
def rcon():
    global_server = MinecraftServer()

    with global_server.run_server() as rcon:
        yield rcon


@pytest.fixture(scope="session")
def test_world():
    return MCWorld("server/world")
