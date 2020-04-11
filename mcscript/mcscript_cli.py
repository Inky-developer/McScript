from argparse import ArgumentParser
from functools import partial
from os.path import exists, isfile, join, normpath
from pathlib import Path
from time import perf_counter

from mcscript import Logger
from mcscript.compile import compileMcScript
from mcscript.data.Config import Config
from mcscript.utils.cmdHelper import MCPATH, generateFiles, getWorld
from mcscript.utils.precompileInstructions import getPrecompileInstructions

"""
A command line interface for mcscript. WIP.
"""


def main():
    """
    A command line interface for mcscript. Work in progress.

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
        "input",
        help="Set the input file",
    )

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
        default="McScript",
        help="Set the name for the datapack. Defaults to 'McScript'"
    )

    parser.add_argument(
        "-c", "--config",
        dest="config",
        nargs="?",
        help="Set the path to the configuration file"
    )

    parser.add_argument(
        "-v", "--verbose",
        dest="verbose",
        action="store_true",
        help="Switch to verbose mode"
    )

    args = parser.parse_args()

    input_ = args.input
    if not exists(input_) or not isfile(input_):
        Logger.critical("Could not open the input file", input_)
        return 0
    with open(input_) as f:
        precompile_instructions = getPrecompileInstructions(f.read())

    output = args.dir or precompile_instructions.get("outpath", None)
    world = None
    mcpath = join(args.mcdir, "saves") if args.mcdir else normpath(precompile_instructions.get("mcpath", MCPATH))

    # ToDo add default config that does not create a file
    config = Config(args.config or ".config.ini")

    start_time = perf_counter()

    if not output:  # if no directory is given, save as a datapack
        worldPath = args.world or precompile_instructions.get("world", None)
        if not worldPath:
            Logger.critical("A World must be specified!")
            return False

        world = getWorld(worldPath, mcpath)

        if world is None:
            Logger.critical(f"Could not find World '{args.world}'")
            return False

    if not exists(input_):
        Logger.critical(f"Could not find file '{input_}'")
        return False

    Logger.info("Compiling...")
    with open(input_, encoding="utf-8") as f:
        # noinspection PyTypeChecker
        datapack = compileMcScript(f.read(), partial(on_compile_status, args), config)

    Logger.info(f"Compiled in {perf_counter() - start_time} seconds")

    if output:
        datapack.write(args.name, Path(output))
    else:
        generateFiles(world, datapack, args.name)

    Logger.info(f"Done in {perf_counter() - start_time} seconds")

    return True


def on_compile_status(_, msg, progress, interim_result):
    Logger.info(f"{msg}... {progress * 100}%")
    Logger.debug(interim_result if hasattr(interim_result, "pretty") else interim_result)


# noinspection PyUnusedLocal
def testDocstrings(a: int, b):
    """
    *italic*
    **bold**
    ``monospace``
    link_
    example_

    A reference to `variable`

    bullet list:

    - item 1
    - item 2
    - item 3

    enumerated list

    1. first element
    2. seconds element
    3. third element
    #. Auto - enumerated

    Grid table:

    +------------+------------+-----------+
    | Header 1   | Header 2   | Header 3  |
    +============+============+===========+
    | body row 1 | column 2   | column 3  |
    +------------+------------+-----------+
    | body row 2 | Cells may span columns.|
    +------------+------------+-----------+
    | body row 3 | Cells may  | - Cells   |
    +------------+ span rows. | - contain |
    | body row 4 |            | - blocks. |
    +------------+------------+-----------+

    ------------

    Simple table:

    =====  =====  ======
       Inputs     Output
    ------------  ------
      A      B    A or B
    =====  =====  ======
    False  False  False
    True   False  True
    False  True   True
    True   True   True
    =====  =====  ======

    -a            command-line option "a"
    -b file       options can have arguments
                  and long descriptions
    --long        options can be long also
    --input=file  long options can also have
                  arguments
    /V            DOS/VMS-s

    .. _link: https://www.google.de
    .. _example:
        Example crossreference target

    Parameters:
        a: a Parameter
        b: another Parameter
    """


if __name__ == '__main__':
    if not main():
        quit(-1)
