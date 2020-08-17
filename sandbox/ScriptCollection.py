import sys
from os import getcwd
from os.path import join

from mcscript import Logger
from mcscript.compile import compileMcScript
from mcscript.data.Config import Config
from mcscript.utils import rcon
from mcscript.utils.cmdHelper import generate_datapack, getWorld

# fix for vscode dont know what exactly is wrong
sys.path.insert(0, ".")


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

code_range = r"""
struct Range {
    min: Int
    max: Int
    current: Int

    fun new(min: Int, max: Int) -> Range {
        Range(min-1, max, min)
    }
    
    fun until(max: Int) -> Range {
        Range.new(0, max)
    }

    fun next(self) -> Tuple {
        self.current += 1
        (self.current, self.current < self.max)
    }
}

let r = Range.until(15)

do {
    let result = r.next()
    let (value, valid) = result
    run for @a { print("{}: {}", value, value * value) }
} while valid
"""

code_temp = """

"""

if __name__ == '__main__':
    mcDir = join(getcwd(), "server")
    world = getWorld("McScript", mcDir)

    config = Config("config.ini")
    config.world = world

    code = code_range
    # code = getScript("math")
    config.input_file = code

    datapack = compileMcScript(config, lambda a, b, c: Logger.info(f"[compile] {a}: {round(b * 100, 2)}%"))
    generate_datapack(config, datapack)
    rcon.send("reload")
