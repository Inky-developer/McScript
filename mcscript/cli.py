import sys
from pathlib import Path
from typing import Optional

import click

from mcscript.compile import compileMcScript
from mcscript.data.Config import Config
from mcscript.utils.cmdHelper import generate_datapack, MCWorld


@click.group()
def main():
    """
    The McScript compiler.

    To quickly build a project run BUILD in "wold/datapacks/src".
    McScript will compile the src directory and write the output in the datapacks directory.

    Compile a single .mcscript file with COMPILE <file.mcscript> <OutDir> <Options>
    """
    pass


@main.command()
@click.option("--release", "-r", is_flag=True, help="Whether to compile in release mode")
def build(release: bool):
    """
    Builds the mcscript files of this project and writes the datapack

    This command should be run in the src directory of a datapack:
        world/datapacks/your_datapack/src

    The output directory will be:
        world/datapacks/your_datapack
    """
    cwd = Path.cwd().absolute()

    config_path = cwd.joinpath("config.config")
    if config_path.exists():
        config = Config(str(config_path))
    else:
        config = Config()

    level_dat = cwd.joinpath("../../../level.dat").resolve()
    if not level_dat.exists():
        click.echo(f"Invalid project. Could not find level.dat file at {click.format_filename(str(level_dat))}",
                   err=True)
        sys.exit(1)

    world = MCWorld(level_dat)
    config.world = world

    src_path = cwd.joinpath("main.mcscript")
    if not src_path.exists():
        click.echo(f"Could not find the main src file at {click.format_filename(str(src_path))}", err=True)
        sys.exit(1)

    project_name = cwd.parent.name
    config.project_name = project_name

    if release:
        config.is_release = True

    with open(src_path) as f:
        input_file = f.read()

    config.input_file = input_file
    datapack = compileMcScript(config)

    generate_datapack(config, datapack)

    click.echo(f"Successfully built project {config.project_name}")


# noinspection PyShadowingBuiltins
@main.command()
@click.argument("input", type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.argument("output", type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True))
@click.option("--name", "-n", envvar="MCSCRIPT_NAME", type=str)
@click.option("--release/", "-d", default=False, is_flag=True, help="Whether to compile in release mode")
@click.option("--mc-version", envvar="MCSCRIPT_MCVERSION", type=str,
              help="The target minecraft version. If not specified latest full-release")
@click.option("--config", help="The config file",
              type=click.Path(exists=True, dir_okay=False, writable=True, resolve_path=True))
def compile(input: str, output: str, name: str, release: bool, mc_version: Optional[str],
            config: Optional[str]):
    """
    Compiles the INPUT and writes the result to OUTPUT directory
    """

    # def on_compile_progress(step: str, progress: float, _prev_input: Any):
    #     pass

    config = Config(config)

    if name is not None:
        config.project_name = name

    if release:
        config.is_release = True

    if mc_version is not None:
        config.minecraft_version = mc_version

    with open(input, encoding="utf-8") as f:
        input_file = f.read()

    config.input_file = input_file
    config.output_dir = output

    datapack = compileMcScript(config)

    generate_datapack(config, datapack)

    click.echo(f"Compiled successfully to {click.format_filename(config.output_dir)}")


@main.command()
def doc():
    click.echo("Doc")
    click.echo("Not Implemented", err=True)


if __name__ == '__main__':
    main()
