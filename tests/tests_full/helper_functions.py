import re
from pathlib import Path
from typing import Tuple, Optional

from mcrcon import MCRcon

from mcscript import Logger
from mcscript.compile import compileMcScript
from mcscript.data.Config import Config
from mcscript.utils.cmdHelper import MCWorld, generate_datapack

TEST_TEMPLATE = """
fun test() -> Bool {{
    {}
}}

set_score("mcscript_test", "result", test())
"""

RESULT_PATTERN = re.compile(r"result has (\d+)")


def run_code(rcon: MCRcon, test_world: MCWorld, code: str) -> Tuple[Optional[int], str]:
    config = Config()
    config.output_dir = Path(test_world.getDatapackPath()) / "mcscript"
    config.input_string = TEST_TEMPLATE.format(code)
    datapack = compileMcScript(config)
    Logger.info(datapack.getMainDirectory().getPath("functions").files)
    generate_datapack(config, datapack)

    rcon.command("reload")
    result = rcon.command(f"scoreboard players get result mcscript_test")

    match = RESULT_PATTERN.match(result)
    if match is not None:
        value = int(match.group(1))
    else:
        value = None

    return value, result
