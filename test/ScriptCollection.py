from src.mcscript import compileMcScript, generateFiles
from src.mcscript.data.Config import Config
from src.mcscript.utils.cmdHelper import getWorld
from test.server import rcon

code_fun = """
fun sum_and_square(a: Number, b: Number) {
    myFancyVar = a + b
    return myFancyVar * myFancyVar    
}

ergebnis = sum_and_square(6,6) + 6
for @a print(ergebnis)
"""

code_if = """
a = 1
if a == 0 {
    a = 1
} else {
    a = 2
}
"""

# currently only end-recursion functions properly
# nope recursion doesn't work
# there is not even an error message (ToDo)
code_fac_rec = """
fun fac(n) {
    if n==1
        return 1
    else
        return n * fac(n-1)
}
ergebnis = fac(1)
"""

code_fac = """
fun fac(n: Number) {
    ret = 1
    while n > 1 {
        ret = ret * n
        for @a print("Zwischenergebnis: ", ret)
        n = n - 1
    }
    return ret
}

ergebnis = fac(3)
for @a print("Ergebnis: ", ergebnis)
"""

code_tick = """
fun printZeroPaddedTime(hours: Number, minutes: Number, seconds: Number) {
    if seconds > 9 {
        if minutes > 9 {
            if hours > 9 {
                actionbar(hours, ":", minutes, ":", seconds)
            } else {
                actionbar("0", hours, ":", minutes, ":", seconds)
            }
        } else {
            if hours > 9 {
                actionbar(hours, ":0", minutes, ":", seconds)
            } else {
                actionbar("0", hours, ":0", minutes, ":", seconds)
            }
        } 
    } else {
        if minutes > 9 {
            if hours > 9 {
                actionbar(hours, ":", minutes, ":0", seconds)
            } else {
                actionbar("0", hours, ":", minutes, ":0", seconds)
            }
        } else {
            if hours > 9 {
                actionbar(hours, ":0", minutes, ":0", seconds)
            } else {
                actionbar("0", hours, ":0", minutes, ":0", seconds)
            }
        } 
    }
}

fun zeroPadHoursMinutes(hours: Number, minutes: Number) {
    if hours > 9 {
        if minutes > 9
            actionbar(hours, ":", minutes)
         else 
            actionbar(hours, ":0", minutes)
    } else {
        if minutes > 9
            actionbar("0", hours, ":", minutes)
         else 
            actionbar("0", hours, ":0", minutes)
    }
}

tickCount = 0
fun onTick() {
    for @p {
        daytime = ((run "time query daytime") + 6000) % 24000 # between 0 and 24_000
        hours = daytime / 1000
        rest = daytime % 1000
        minutes = rest * 60 / 1000 # what about transforming 0.6 to 6 / 100? (ToDo)
        seconds = (rest * 60 % 1000) * 60 / 1000
        
        if tickCount % 20 == 0 {
            zeroPadHoursMinutes(hours, minutes)
        }
        #actionbar("0.", tickCount % 20 * 5)
        tickCount += 1
    }
}
"""

code_enum = """
enum block {
    dirt = 1;
    coblestone;
}
for @a print(block.dirt)
"""

code_block = """
me = @s

tickCount = 0
fun onTick() {
    for @a at me {
        if tickCount % 20 == 0
            actionbar(me, " Sekunde: ", tickCount / 20)
    }
    tickCount += 1
}
"""

code_text = """
player = @p
for player {
    print("Hallo ", player, ", 1+1=", 1+1)
    title("Hallo ", player, ", 1+1=", 1+1)
    subtitle("Hallo ", player, ", 1+1=", 1+1)
    actionbar("Hallo ", player, ", 1+1=", 1+1)
}
"""

code_rotation = """
fun onTick() {
    for @a {
        rotation = ((run "data get entity @s Rotation[0]") + 360) % 360
        direction = (rotation + 23) % 360 / 45 % 8
        if direction == 0 actionbar("Süd - ", rotation, "°")
        else if direction == 1 actionbar("Süd-West - ", rotation, "°")
        else if direction == 2 actionbar("West - ", rotation, "°")
        else if direction == 3 actionbar("Nord-West - ", rotation, "°")
        else if direction == 4 actionbar("Nord - ", rotation, "°")
        else if direction == 5 actionbar("Nord-Ost - ", rotation, "°")
        else if direction == 6 actionbar("Ost - ", rotation, "°")
        else if direction == 7 actionbar("Süd-Ost - ", rotation, "°")
        else if direction == 8 actionbar("Süd - ", rotation, "°")
        else actionbar("?")
    }
}
"""

code_math = """
fun pow(a: Number, b: Number) {
    res = 1
    while b > 0 {
        if b % 2 == 1 
            res = res * a
        a = a * a
        b = b / 2        
    }
    return res
}

fun fac(x: Number) {
    ret = 1
    while x > 1 {
        ret = ret * x
        x = x - 1
    }
    return ret
}

for @a {
    a = 5
    b = 3
    print(a, "^", b, " = ", pow(5,3))
    print(a, "! = ", fac(5))
}
"""

code_block_get = """
fun onTick() {
    for @p at @s {
        block = getBlock(0, "-0.05", 0)
        actionbar(block)
        # actionbar(block)
        if setBlock(block, 0, 10, 0) == 0
            actionbar("Could not place block!")
    }
}
"""

code_block_fill = """
active = 0
i = 0

for @p at @s {
    run "execute align xz positioned ~.5 ~ ~.5 run tp @s ~ ~ ~"
    run "tp @s ~ 1 ~"
}

 
fun onTick() {
    if active {
        for @p at @s {
            setBlock(blocks.dirt, 0, -1, 0)
            setBlock(i)
            if i % 151 == 0 {
                print("back")
                run "tp @s ~-150 ~ ~1"
            }
            i = i+1
            run "tp @s ~1 ~ ~"
        }
    }
}
"""

code_block_rotation = """
block=blocks.dragon_head;rot=0active=1fun onTick(){if isBlock(blocks.air,0,2,0)active=0else if isBlock(blocks.dragon_head,0,2,0)active=1if active{setBlock(block+rot,0,2,0)rot=(rot+1)%16}}
"""

code_operator_ip = """
a = 0
a += 5
for @a print(a)

fun onTick() {
    a *= 2
    if a != 0 for @a print(a)
}
"""

code_const = """
const block = blocks.player_head
for @a print(isBlock(block))
"""

code_ran = """
ones = 0
zeros = 0
fun onTick() {
    i = 0
    while i < 100 {
        rand = random(1) % 2
        if (rand == 1) ones += 1 else zeros += 1
        onesVsZeros = ones * 1000 / zeros
        zerosVsOnes = zeros * 1000 / ones
        if onesVsZeros < 1000 {
            for @a actionbar(ones, " ", zeros, " 0.", onesVsZeros)
        } else {
            for @a actionbar(ones, " ", zeros, " 0.", zerosVsOnes)
        }
        i += 1
    }
}
"""

code_test_ran = """
random()
random(1)
random()
random(1)
"""

code_randint = """
fun randint(min: Number, max: Number) {
    return random() % (max - min) + min
}

fun onTick() { 
    for @a print(randint(10, 20))
}
"""

code_test_limit = """
i = 0
while 1 == i
    i += 1
"""

code_fixed_point = """
a = 1.5
b = 2.75

for @a {
    print(a, " + ", b, " = ", a+b)
    print(a, " - ", b, " = ", a-b)
    print(a, " * ", b, " = ", a*b)
    print(a, " / ", b, " = ", a/b)
    print(a, " % ", b, " = ", a%b)
}
"""

code_mandelbrot = """
const xMin = -2.0
const xMax = 0.5
const yMin = -1.25
const yMax = 1.25

const maxIterations = 20
const size = 50

x = xMin
y = yMin
shouldRun = 0

fun createMandelbrot() -> Null {
    x2 = x
    y2 = y
    i = 0
    abs = x2*x2 + y2*y2
    while (i < maxIterations) * (abs < 4.0)  {
        i += 1
        xTemp = x2*x2 - y2*y2 + x
        y2 = 2.0 * x2 * y2 + y
        x2 = xTemp
        abs = x2*x2 + y2*y2
    }
    if abs < 4.0 {
        setBlock(blocks.black_wool, 0, -1, 0)
    } else {
        if i < 1
            setBlock(blocks.white_concrete, 0, -1, 0)
        else if i <= 2
            setBlock(blocks.light_gray_concrete, 0, -1, 0)
        else if i <= 4
            setBlock(blocks.yellow_concrete, 0, -1, 0)
        else if i <= 6
            setBlock(blocks.orange_concrete, 0, -1, 0)
        else if i <= 8
            setBlock(blocks.lime_concrete, 0, -1, 0)
        else if i <= 10
            setBlock(blocks.green_concrete, 0, -1, 0)
        else if i <= 12
            setBlock(blocks.cyan_concrete, 0, -1, 0)
        else if i <= 14
            setBlock(blocks.light_blue_concrete, 0, -1, 0)
        else if i <= 16
            setBlock(blocks.blue_concrete, 0, -1, 0)
        else if i <= 18
            setBlock(blocks.red_concrete, 0, -1, 0)
        else if i <= 20
            setBlock(blocks.gray_concrete, 0, -1, 0)
    }
}

fun onTick() -> Null {
    for @p at @s {
        if shouldRun {
            print(x, ", ", xMax)
            createMandelbrot()
            if x < xMax {
                x += (xMax - xMin) / size
                execute("tp @s ~1 ~ ~")
            } else {
                x = xMin
                execute(stringFormat("tp @s ~-$ ~ ~1", size))
                y += (yMax - yMin) / size
                if y > yMax
                    shouldRun = 0
            }
        }
    }
}

"""

code_string_replacement = """
const block = "stone"
for @a at @s print(execute(stringFormat("setblock ~ ~ ~ $", block)))
"""

code_weather = """
fun onTick() -> Null {
    for @a {
        if isThundering() {
            actionbar("Thunder")
        } else if isRaining() {
            actionbar("Rain")
        } else {
            actionbar("Clear Weather")
        }
    }
}
"""

code_light = """
fun onTick() -> Null {
    for @a actionbar("Light level: ", getLightLevel())
}
"""

code_biome = """
fun onTick() -> Null {
    for @a actionbar("The current biome id is: ", getBiome())
}
"""

code_environment = """
fun onTick() -> Null {
    for @a {
        lightlevel = getLightLevel()
        biome = getBiome()
        if isThundering() {
            actionbar("Thunder, biomeId: ", biome, ", lightlevel: ", lightlevel)
        } else if isRaining() {
            actionbar("Rain, biomeId: ", biome, ", lightlevel: ", lightlevel)
        } else {
            actionbar("Clear Weather, biomeId: ", biome, ", lightlevel: ", lightlevel)
        }
    }
}
"""

code_mark_feature = """
const feature = features.fortress
const markerBlock = blocks.white_stained_glass
const entityId = "mcscript_feature_detector"
const summonString = "summon minecraft:area_effect_cloud ~$ ~$ ~$ {Duration:2147483647,Tags:['$']}"
execute("kill @e[tag=$entityId]")
for @p at @s {
    execute(stringFormat(summonString, "", "", "", entityId))
}

# checks all adjacent blocks if they are in the features bounding box.
fun checkBlocks() -> Null {
    if isFeature(feature) == 0 {
        execute("kill @s")
    } else if isBlock(markerBlock) == 0 {
        setBlock(markerBlock)
        execute(stringFormat(summonString, 0, 0, 1, entityId))
        execute(stringFormat(summonString, 0, 0, -1, entityId))
        execute(stringFormat(summonString, 0, 1, 0, entityId))
        execute(stringFormat(summonString, 0, -1, 0, entityId))
        execute(stringFormat(summonString, 1, 0, 0, entityId))
        execute(stringFormat(summonString, -1, 0, 0, entityId))
    } else {
        execute("kill @s")
    }
}

shouldRun = 0
finished = 0
fun doTick() -> Null {
    if (finished == 0) * (evaluate("execute unless entity @e[tag=$entityId]")) {
        for @a print("Finished.")
        finished = 1
    }
    if finished == 0 {
        for @a actionbar("Running...")
        # ToDo: better selectors
        for @e[tag=mcscript_feature_detector,limit=250] at @s {
            checkBlocks()
        }
    }
}

fun onTick() -> Null {
    if shouldRun doTick()
}
"""

code_temp = """
a = -1
a = -a
"""

if __name__ == '__main__':
    world = getWorld("McScript", r"D:\Dokumente\Informatik\Python\McScript\test\server")
    config = Config("config.ini")
    config.get("name")
    datapack = compileMcScript(code_temp, lambda a, b, c: print(f"{a}: {b * 100}%"), config)
    generateFiles(world, datapack)
    rcon.send("reload")
