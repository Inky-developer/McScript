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
