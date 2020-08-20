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
let x_min = -1.8
let x_max = 0.7
let y_min = -1.25
let y_max = 1.25

let size = 32.0
let x_step = (x_max - x_min) / size
let y_step = (y_max - y_min) / size

let max_iterations = 20
let marker_name = "mandelbrot_marker"


fun in_mandelbrot(x: Fixed, y: Fixed) -> Bool {
    let x2 = .0
    let y2 = .0
    let x0 = x
    let y0 = y
    let i = 0
    
    while x2 + y2 < 4.0 and i < max_iterations {
        y = x * y * 2.0 + y0
        x = x2 - y2 + x0
        x2 = x*x
        y2 = y*y
        i += 1
    }
    
    i < max_iterations
}

let should_run = false
fun on_tick() {
    should_run = evaluate("execute if entity @e[tag=$marker_name]") == 1
    
    if should_run {
        run at @e[tag=$marker_name] {
            let current_x = x_min
            let current_y = y_min
            
            let i = 0.0
            while i < size local 0, 0, 1 {
                let j = 0.0
                
                while j < size local 1, 0, 0 {
                    if in_mandelbrot(current_x, current_y) {
                        execute("setblock ~ ~-1 ~ black_concrete")
                    } else {
                        execute("setblock ~ ~-1 ~ white_concrete")
                    }
                    current_x += x_step
                    j += 1.0
                }
                
                current_y += y_step
                i += 1.0
            }
        }
        
        execute("kill @e[tag=$marker_name]")
    }
}
"""

if __name__ == '__main__':
    mcDir = join(getcwd(), "server")
    world = getWorld("McScript", mcDir)

    config = Config("config.ini")
    config.world = world

    code = code_temp
    # code = getScript("mandelbrot")
    config.input_string = code

    datapack = compileMcScript(config, lambda a, b, c: Logger.info(f"[compile] {a}: {round(b * 100, 2)}%"))
    generate_datapack(config, datapack)
    rcon.send("reload")
