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
string = "hello :)";
execute("say This is a testring $string")

fun test() -> Number {
    a = 1
    return a
}

run for @a {
    # print(string);
    # print(string.length);
    # if (string) {
    #     print("String has value!");
    # } else {
    #     print("String has no value!");
    # }
    # 
    # for (i in range(string.length)) {
    #     print(string[i]);
    # }
    # 
    # 
    # a = "abc: "
    # b = a + 1
    # print(a)
    # print(b)
    # 
    # # ToDo: String comparison
    # print(b + string)
    # 
    # for (char in string) {
    #     print(char);
    # }
    
    result = test()
    print(result)
}
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
