from src.mcscript import compileMcScript, generateFiles
from src.mcscript.data.Config import Config
from src.mcscript.utils.cmdHelper import getWorld
from test.scripts import getScript
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
struct Complex {
    real: Fixed
    imag: Fixed

    fun add(self: Complex, other: Complex) -> Complex {
        return Complex(self.real + other.real, self.imag + other.imag)
    }

    fun square(self: Complex) -> Complex {
        return Complex(self.real * self.real - self.imag * self.imag, 2.0 * self.real * self.imag)
    }

    fun absSquared(self: Complex) -> Fixed {
        return self.real * self.real + self.imag * self.imag
    }
    
    fun print(self: Complex) -> Null {
        print(self.real, " + ", self.imag, "i")
    }
}

run for @a {
    c1 = Complex(1.5, 2.5)
    c2 = Complex(-5.0, 8.5)
    
    c1.print()
    c2.print()
    
    c3 = c1.add(c2)
    c3.print()
    
    sq = c3.absSquared()
    print(sq)
}
"""

if __name__ == '__main__':
    world = getWorld("McScript", r"D:\Dokumente\Informatik\Python\McScript\test\server")
    config = Config("config.ini")
    config.get("name")
    # code = code_temp
    code = getScript("math")
    datapack = compileMcScript(code, lambda a, b, c: print(f"{a}: {b * 100}%"), config)
    generateFiles(world, datapack)
    rcon.send("reload")
