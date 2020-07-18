"""
A command line interface for mcscript.
"""
import re
import sys
from argparse import ArgumentParser
from functools import partial
from os import makedirs
from os.path import exists, isfile, normpath, split
from pathlib import Path
from time import perf_counter

from mcscript import Logger
from mcscript.assets import setCurrentData
from mcscript.compile import compileMcScript
from mcscript.data.Config import Config
from mcscript.documentation import generate_json
from mcscript.utils.cmdHelper import MCPATH, generateFiles, getWorld, getWorlds, setCurrentWorld
from mcscript.utils.precompileInstructions import getPrecompileInstructions


def main():
    """
    A command line interface for mcscript.

    There are currently three methods to specify what should happen with the input file:
        - The config file, lowest priority
        - The call arguments, medium priority
        - precompile instructions, highest priority

    Command line Parameters:
        The first argument must be the mcscript input file.

        -m         Sets the worlds directory for minecraft. Default %AppData%/.minecraft/saves
        -w         Sets the output world by world name mutually exclusive to -d
        -d         Sets the output directory.
        -n         Sets the name for the datapack, default McScript
        -c         Sets the path to the config file, optional
        -v         Sets the verbose flag to true
    """
    parser = ArgumentParser(prog="McScript")

    parser.add_argument(
        "action",
        help="what action to execute",
        choices=["build", "gen_data"]
    )

    parser.add_argument(
        "input",
        help="Set the input file (output file if gen_data)",
    )

    # arguments only for build
    parser.add_argument(
        "-m", "--mcdir",
        dest="mcdir",
        nargs="?",
        help="Set the path to .minecraft. Defaults to '%%AppData%%\\.minecraft\\saves\\'"
    )

    directory_group = parser.add_mutually_exclusive_group()
    directory_group.add_argument(
        "-w", "--world",
        dest="world",
        nargs="?",
        help="Select a minecraft world to create a datapack there."
    )

    directory_group.add_argument(
        "-d", "--dir",
        dest="dir",
        nargs="?",
        help="Set the output directory"
    )

    parser.add_argument(
        "-n", "--name",
        dest="name",
        nargs="?",
        default="mcscript",
        help="Set the name for the datapack. Defaults to 'McScript'"
    )

    parser.add_argument(
        "-c", "--config",
        dest="config",
        nargs="?",
        help="Set the path to the configuration file"
    )

    args = parser.parse_args()
    if args.action == "build":
        return run_build(args)
    if args.action == "gen_data":
        return run_gen_data(args)

    Logger.critical("Could not determine what action to execute")
    return False


def run_gen_data(args):
    output = args.input  # yeah

    start_time = perf_counter()
    json = generate_json(Config(args.config or None))
    Logger.info(f"Generated json in {perf_counter() - start_time:.4f} seconds")

    path, file = split(output)
    if not exists(path):
        makedirs(path)

    with open(output, "w+", encoding="utf-8") as f:
        Logger.debug(f"writing {len(json) / 1024:.2f} kbytes.")
        f.write(json)

    Logger.debug("Generated:\n" + json)

    return True


def run_build(args):
    # read input file for custom instructions
    input_ = args.input
    if not exists(input_) or not isfile(input_):
        Logger.critical(f"Could not open the input file {input_}")
        return 0
    with open(input_) as f:
        precompile_instructions = getPrecompileInstructions(f.read())

    # the output directory will be used if no world is specified
    output = precompile_instructions.get("outpath", None) or args.dir

    world = None
    # first try to get the path from the input file, then from the call parameters, last use default directory
    mcpath = normpath(precompile_instructions.get("mcpath", args.mcdir or MCPATH))

    if output and ("mcpath" in precompile_instructions or args.mcdir):
        Logger.critical("Outpath and mcpath are mutually exclusive but both specified.")
        return False

    config = Config(args.config or None)
    name = precompile_instructions.get("name", args.name)
    if name is not None:
        if not re.match(r"^[a-z_]+$", name) or len(name) > 12:
            Logger.critical(
                f"Invalid name '{name}': May only contain letters and underscores and less than 13 characters.")
            return False
        config["compiler"]["name"] = name

    start_time = perf_counter()

    if not output:  # if no directory is given, save as a datapack
        worldPath = precompile_instructions.get("world", None) or args.world
        if not worldPath:
            Logger.critical("A World must be specified!")
            return False

        try:
            world = getWorld(worldPath, mcpath)
            setCurrentWorld(world)
        except ValueError:
            Logger.critical(f"Could not find World '{worldPath}'")
            Logger.info(f"Available worlds at {mcpath}:\n{list(getWorlds(mcpath))}")
            return False

        # if the world is specified use the data version that matches
        setCurrentData(str(world.mcVersion["Name"]))

    if not exists(input_):
        Logger.critical(f"Could not find file '{input_}'")
        return False

    Logger.info("Compiling...")
    with open(input_, encoding="utf-8") as f:
        # noinspection PyTypeChecker
        datapack = compileMcScript(f.read(), partial(on_compile_status, args), config)

    Logger.info(f"Compiled in {perf_counter() - start_time:.3f} seconds")

    if output:
        # make output dir if not exists
        if not exists(output):
            makedirs(output, exist_ok=True)
        datapack.write(args.name, Path(output))
    else:
        generateFiles(world, datapack, args.name)

    Logger.info(f"Done in {perf_counter() - start_time} seconds")

    return True


def on_compile_status(_, msg, progress, interim_result):
    Logger.info(f"{msg}... {progress * 100}%")


if __name__ == '__main__':
    if not main():
        Logger.critical("Quitting..")
        sys.exit(1)
