from os import getcwd
from os.path import join

from mcscript import Logger
from mcscript.assets import setCurrentData
from mcscript.compile import compileMcScript
from mcscript.data.Config import Config
from mcscript.utils import rcon
from mcscript.utils.cmdHelper import generateFiles, getWorld


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

code_temp = """
y = 0
fun onTick() {
    if (hasEntity(@e[type=armor_stand])) {
        run for @e[type=armor_stand] {
            new_y = evaluate("data get entity @s Pos[1]")
            if (new_y < y) y = new_y
        }
    }
    run for @a actionbar(y)
}
"""

if __name__ == '__main__':
    world = getWorld("McScript", join(getcwd(), "server"))
    # world = getWorld("McScript")
    setCurrentData(str(world.mcVersion["Name"]))
    config = Config("config.ini")
    # config.get("name")
    # code = code_temp
    code = getScript("clock")
    datapack = compileMcScript(code, lambda a, b, c: Logger.info(f"[compile] {a}: {round(b * 100, 2)}%"), config)
    generateFiles(world, datapack)
    rcon.send("reload")
