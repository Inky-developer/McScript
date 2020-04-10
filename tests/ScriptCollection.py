from os import getcwd
from os.path import join

from mcscript import Logger
from mcscript.compile import compileMcScript
from mcscript.data.Config import Config
from mcscript.utils.cmdHelper import getWorld, generateFiles
from tests.server import rcon

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
struct Test {
    a: Number;
    b: Number;
}
t = Test(1, 2)

return t.a == 1 and t.b == 2;
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
