import sys

from cx_Freeze import Executable, setup

sys.path.insert(0, "../")
from mcscript import __version__
from mcscript.lang.builtins import iterBuiltins

# builtins are not recognized by cxFreeze
builtin_modules = [f"mcscript.lang.builtins.{builtin}" for builtin in iterBuiltins()]
print("Included builtins:")
print(builtin_modules)

setup(
    name="McScript",
    version=__version__.__version__,
    description='A Simple and powerful datapack generator for minecraft',
    executables=[Executable("../mcscript.py", base=None)],
    options={
        "build_exe": {
            # fix this: cx_freeze does not automatically include all nbt files
            "includes": ["mcscript", "nbt.world"] + builtin_modules,
            "path"    : sys.path + ["../"],
            "optimize": 2
        }
    }
)
