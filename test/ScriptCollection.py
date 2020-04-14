from os import getcwd
from os.path import join

from mcscript import Logger
from mcscript.compile import compileMcScript
from mcscript.data.Config import Config
from mcscript.utils import rcon
from mcscript.utils.cmdHelper import generateFiles, getWorld

# test to see if this is tracked
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
a = "this is a test string";
"""

if __name__ == '__main__':
    world = getWorld("McScript", join(getcwd(), "server"))
    config = Config("config.ini")
    # config.get("name")
    code = code_temp
    # code = getScript("mandelbrot")
    datapack = compileMcScript(code, lambda a, b, c: Logger.info(f"[compile] {a}: {round(b * 100, 2)}%"), config)
    generateFiles(world, datapack)
    rcon.send("reload")
