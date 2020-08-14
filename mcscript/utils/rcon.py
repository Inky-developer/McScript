"""
Simple Rcon module.
If a server runs on localhost with rcon enabled and port and password set as below, unit tests will test the datapack
on this server automatically
"""
import atexit

from mcrcon import MCRcon

HOST = "localhost"
PORT = 25575
PASSWORD = "1234"

connected: bool = False
rcon: MCRcon = MCRcon(HOST, PASSWORD, PORT)
atexit.register(rcon.disconnect)


def createConnection():
    global connected
    if not connected:
        rcon.connect()
        connected = True


def send(command: str) -> str:
    createConnection()
    return rcon.command(command)
