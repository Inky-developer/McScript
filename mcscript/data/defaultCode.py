# from __future__ import annotations

# from mcscript import Logger
# from mcscript.utils.Datapack import Datapack


# def addDefaults(datapack: Datapack) -> Datapack:
#     addDynamicDefaults(datapack)
#     return datapack


# def addDynamicDefaults(datapack: Datapack) -> Datapack:
#     # adds functions
#     files = datapack.getMainDirectory().getPath("functions").files
#     for default in DEFAULTS:
#         files.push(f"{default}.mcfunction")
#         try:
#             text = DEFAULTS[default](datapack, files.pois)
#         except KeyError:
#             # script does not have to contain every "magic" function
#             continue
#         files.get().write(text)
#         Logger.info(f"[DefaultCode] wrote file {default}.mcfunction")
#     return datapack


# # ToDO re-add this
# MAGIC_FUNCTIONS = {
#     # "onTick": 0
# }
# """
# A lookup table for the compiler. Keys are all magic functions and the values are the number of required parameters.
# """


# def tick(datapack: Datapack, pois) -> str:
#     statements = []
#     if fn := pois.get("onTick", None):
#         statements.append(Command.RUN_FUNCTION(function=fn[1]))
#     if getattr(datapack.getMainDirectory(), "hasSubTickClock", False):
#         statements.insert(0, "worldborder set 59999000")
#         statements.insert(1, "worldborder add 1000 1")
#     return multiple_commands(*statements)


# # noinspection SpellCheckingInspection
# DEFAULTS = {
#     # "tick": tick
# }
