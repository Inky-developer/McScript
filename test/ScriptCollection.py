from os import getcwd
from os.path import join

from mcscript import Logger
from mcscript.assets import setCurrentData
from mcscript.compile import compileMcScript
from mcscript.data.Config import Config
from mcscript.utils import rcon
from mcscript.utils.cmdHelper import generateFiles, getWorld, setCurrentWorld


def getScript(name: str) -> str:
    with open(join("../examples/", name + ".mcscript"), encoding="utf-8") as f:
        return f.read()


code_array = """
struct Vec3 {
    x: Number
    y: Number
    z: Number
}

run for @a at @s {
    a = array(2)
    print(a[0])
    print(a[1])
    
    a[0] = 1
    a[1] = 2
    
    print(a[0])
    print(a[1])
    
    for (i in a) {
        print(i)
    }
    
    nonStatic = 4
    for (i in arrayOf("This", "is", "an", "example", "array!", nonStatic)) {
        print(i)
    }
    
    a = 1
    b = 2
    c = 3
    array = arrayOf(a, b, c)
    c = 4
    print("Array: ", array)
    
    pos = Vec3(10, 12, 14)
    print(pos);
}

fun make_disk() -> Null {
    const r = 100
    for (x in range(-r, r+1)) {
        for (z in range(-r, r+1)) {
            if (x*x + z*z < r*r) {
                setBlock(blocks.red_stained_glass, x, 0, z);
            }
        }
    }
}
"""

code_temp = r"""
# s = "Hallo, Welt!"
# 
# while (s.length < 100) {
#     s += " Was ein Tag!"
#     # s[0] = s[1]
# }
# run for @a print("The length of string '[b]{}[/]' is: {}", s, s.length)
# 
# _DebugVariable("s")

a = 0
while (a < 5) {
    a += 1
}
"""

if __name__ == '__main__':
    mcDir = join(getcwd(), "server")
    # mcDir = r"C:\Users\david\AppData\Roaming\.minecraft\Entwicklungsversionen\saves"
    # world = getWorld("20w18a", mcDir)
    world = getWorld("McScript", mcDir)
    setCurrentWorld(world)

    setCurrentData(str(world.mcVersion["Name"]))
    config = Config("config.ini")
    # print(precompileInstructions.getPrecompileInstructions(code_temp))
    # config.get("name")
    code = code_temp
    # code = getScript("mandelbrot")
    datapack = compileMcScript(code, lambda a, b, c: Logger.info(f"[compile] {a}: {round(b * 100, 2)}%"), config)
    generateFiles(world, datapack)
    rcon.send("reload")
