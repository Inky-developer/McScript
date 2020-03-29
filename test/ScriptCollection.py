from src.mcscript import compileMcScript, generateFiles
from src.mcscript.data.Config import Config
from src.mcscript.utils.cmdHelper import getWorld
from test.server import rcon

code_struct = """
struct Complex {
    real: Fixed
    imag: Fixed
    
    fun multiply(self: Complex, other: Number) -> Null {
        self.real *= other
    } 
}

c = Complex(1.0, 0.0)
run for @a print(c.real)
"""

code_temp = """
a = blocks.stone
blocks.test = 1
"""

if __name__ == '__main__':
    world = getWorld("McScript", r"D:\Dokumente\Informatik\Python\McScript\test\server")
    config = Config("config.ini")
    config.get("name")
    datapack = compileMcScript(code_temp, lambda a, b, c: print(f"{a}: {b * 100}%"), config)
    generateFiles(world, datapack)
    rcon.send("reload")
