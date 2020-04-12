import sys

from cx_Freeze import Executable, setup

sys.path.insert(0, "../")
from mcscript.lang.builtins import iterBuiltins

# builtins are not recognized by cxFreeze
builtin_modules = [f"mcscript.lang.builtins.{builtin}" for builtin in iterBuiltins()]
print("Included builtins:")
print(builtin_modules)

setup(
    name="McScript",
    version="0.1.0",
    description='A Simple and powerful datapack generator for minecraft',
    executables=[Executable("../mcscript/mcscript_cli.py", base=None)],
    options={
        "build_exe": {
            # fix this: cx_freeze does not automatically include all nbt files
            "includes": ["mcscript", "nbt.world"] + builtin_modules,
            "path"    : sys.path + ["../"],
            "optimize": 2
        }
    }
)
