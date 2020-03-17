from argparse import ArgumentParser
from functools import partial
from os.path import join, exists
from time import perf_counter

from src.mcscript import compileMcScript, generateFiles
from src.mcscript.data.Config import Config
from src.mcscript.utils.cmdHelper import MCPATH, getWorld


def main():
    parser = ArgumentParser(prog="McScript")

    parser.add_argument(
        "-i", "--input",
        dest="input",
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
        "-v", "--verbose",
        dest="verbose",
        action="store_true",
        help="Switch to verbose mode"
    )

    args = parser.parse_args()

    input_ = args.input
    output = args.dir
    world = None
    mcpath = join(args.mcdir, "saves") if args.mcdir else MCPATH

    # ToDo add config as an argument
    config = Config(".config.ini")

    starttime = perf_counter()

    if not output:  # if no directory is given, save as a datapack
        if not args.world:
            print("[ERROR] A World must be specified!")
            return False

        world = getWorld(args.world, mcpath)

        if world is None:
            print(f"[ERROR] Could not find World '{args.world}'")
            return False

    if not exists(input_):
        print(f"[ERROR] Could not find file '{input_}'")
        return False

    print("Compiling...")
    with open(input_, encoding="utf-8") as f:
        # noinspection PyTypeChecker
        datapack = compileMcScript(f.read(), partial(on_compile_status, args), config)

    print(f"Compiled in {perf_counter() - starttime} seconds")

    if output:
        datapack.write(args.name, output)
    else:
        generateFiles(world, datapack, args.name)

    print(f"Done in {perf_counter() - starttime} seconds")

    return True


def on_compile_status(args, msg, progress, interim_result):
    print(f"{msg}... {progress * 100}%")
    if args.verbose:
        print(interim_result.pretty() if hasattr(interim_result, "pretty") else interim_result)


if __name__ == '__main__':
    if not main():
        quit(-1)
