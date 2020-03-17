# from src.mcscript.lang import AddressResource

# NAME = "mcscript"
# UTILS = f"{NAME}_utils"


# def get(command, /, **kwargs) -> str:
#     if command in TEMPLATES:
#         return TEMPLATES[command].format(**kwargs)
#     return DYNAMIC_TEMPLATES[command](**kwargs)
#
#
# def _format(dict_):
#     return {key: dict_[key].format(name=NAME, vars=VARS) for key in dict_}


# TEMPLATES = _format({
# push expression stack
# "pes": "scoreboard players set {{stack}} {name} {{value}}",

# binary operation
# "bop": "scoreboard players operation {{stack1}} {name} {{operator}}= {{stack2}} {name}",

# binary operation in place
# "boi": "scoreboard players operation {{stack1}} {vars} {{operator}}= {{stack2}} {name}",

# loadToScoreboard variable
# "lda": "scoreboard players operation {{a}} {name} = {{b}} {vars}",

# sets the return value
# "ret": "scoreboard players operation .ret {name} = {{a}} {name}",

# loads the return value
# "res": "scoreboard players operation {{a}} {name} = .ret {name}",

# gets a scoreboard value
# "get": "scoreboard players get {{a}} {name}",

# calls a function
# "cal": "function {name}:{{function}}",

# calls a function if a is one
# "cio": "execute if score {{a}} {name} matches 1 run function {name}:{{function}}",

# calls a function if a is not none
# "cuo": "execute unless score {{a}} {name} matches 1 run function {name}:{{function}}",

# runs a command if a is equal to value
# "rie": "execute if score {{a}} {name} matches {{value}} run {{command}}",

# sets a to zero
# "sez": "scoreboard players set {{a}} {name} 0",

# runs a function and stores the result in a scoreboard
# "run": "execute storeToNbt result score {{address}} {name} run {{command}}",

# Tests for a block
# "tbk": "execute if block {{x}} {{y}} {{z}} {{block}}",

# change execution position
# "eat": "execute at {{target}} run {{command}}",

# change execution target
# "eas": "execute as {{target}} run {{command}}",

# tellraw command
# "tellraw": "tellraw @s {{text}}",

# title command
# "title": "title @s title {{text}}",

# subtitle command
# "subtitle": "title @s subtitle {{text}}",

# actionbar command
# "actionbar": "title @s actionbar {{text}}",

# calls a function
# "runFunction": "function {{name}}:{{function}}",

# tests for a block
# "runIfBlock": "execute if block ~ ~ ~ {{block}} run {{command}}",

# tests for a blocktag
# "runIfBlockTag": "execute if block ~ ~ ~ #{{name}}:{{tag}} run {{command}}",

# "compareValue": "execute if score {{a}} {{name}} matches {{value}} run {{command}}",

# "setBlock": "setblock {{x}} {{y}} {{z}} {{block}}",

# "setEqual": "scoreboard players set {{stack}} {{name}} {{value}}",

# "executePositioned": "execute positioned {{x}} {{y}} {{z}} run {{command}}",

# dont use these
# compare if
# "cmi": "execute if score {{a}} {name} {{operator}} {{b}} {name} run "
#        "scoreboard players set {{c}} {name} 1",
# compare unless -> not equal
# "cne": "execute unless score {{a}} {name} = {{b}} {name} run "
#        "scoreboard players set {{c}} {name} 1"
# })

# DYNAMIC_TEMPLATES = {
#     # set if -> set c to one if the boolean operation between a and b evaluates to 1 otherwise to zero
#     "sei": lambda *, a, operator, b, c: (get("cmi", a=a, operator=operator, b=b, c=c)
#                                          if operator != "!="
#                                          else get("cne", a=a, b=b, c=c)),
#     # set equal
#     "seq": lambda a, b: "scoreboard players operation {a} {vars} = {b} {name}".format(
#         a=a,
#         b=b,
#         vars=VARS,
#         name=NAME
#     ) if isinstance(b, AddressResource) else "scoreboard players set {a} {vars} {b}".format(
#         a=a,
#         b=b,
#         vars=VARS
#     )
# }

# BINARY_OPERATOR = {
#     "TIMES": "*",
#     "DIVIDE": "/",
#     "MODULO": "%",
#     "PLUS": "+",
#     "MINUS": "-"
# }
#
# BINARY_COMPARISON = {
#     "VERIFY_EQUAL": "=",
#     "VERIFY_NOT_EQUAL": "!=",
#     "VERIFY_GREATER": ">",
#     "VERIFY_GREATER_OR_EQUAL": ">=",
#     "VERIFY_LESS": "<",
#     "VERIFY_LESS_OR_EQUAL": "<="
# }
