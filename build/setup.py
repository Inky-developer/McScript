import sys

from cx_Freeze import Executable, setup

setup(
    name="McScript",
    version="0.1.0",
    description='A Simple and powerful datapack generator for minecraft',
    executables=[Executable("../mcscript/mcscript_cli.py", base=None)],
    options={
        "build_exe": {
            # fix this: cx_freeze does not automatically include all nbt files
            "includes": ["mcscript", "nbt.world"],
            "path"    : sys.path + ["../"],
            "optimize": 2
        }
    }
)
