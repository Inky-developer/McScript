import unittest
from os import getcwd
from os.path import join
from shutil import rmtree

from mcscript import Logger
from mcscript.Exceptions.McScriptException import McScriptException
from mcscript.compile import compileMcScript
from mcscript.data.Config import Config
from mcscript.utils.cmdHelper import generateFiles, getWorld
from tests.Language.loadScripts import loadScripts
from tests.server import rcon

TELLRAW_SUCCESS = \
    '/tellraw @a ["",{"text":"["},{"text":"McScript","color":"gold"},{"text":"] "},' \
    '{"text":"All tests successful!",color":"green"}]'
TELLRAW_FAILURE = \
    '/tellraw @a ["",{"text":"["},{"text":"McScript","color":"gold"},{"text":"] "},' \
    '{"text":"Some test(s) failed!","color":"red"}]'


class TestMcLang(unittest.TestCase):
    def setUp(self) -> None:
        self.tests = loadScripts()
        self.wrapper = self.tests.pop("Wrapper")[0]
        self.world = getWorld("McScript", join(getcwd(), "server"))
        self.datapackName = "McScript_tests"
        self.config = Config("config.ini")
        self.config["compiler"]["name"] = "mcscript_tests"

        rmtree(
            join(self.world.getDatapackPath(), self.datapackName),
            onerror=lambda func, path, exc_info: Logger.warning(f"[TestLang] Could not remove {path} {exc_info}")
        )

        self.testCount = 0
        for test in self.tests:
            for _ in self.tests[test]:
                self.testCount += 1

    def tearDown(self) -> None:
        rmtree(
            join(self.world.getDatapackPath(), self.datapackName),
            onerror=lambda func, path, exc_info: Logger.warning("[TestLang] Could not remove ", path, exc_info)
        )

    def testMcLang(self):
        i = 0
        for test in self.tests:
            for index, code in enumerate(self.tests[test]):
                i += 1
                with self.subTest(name=test, index=index):
                    try:
                        code = self.wrapper.format(code, name=test, index=i, count=self.testCount)
                        datapack = compileMcScript(code, lambda a, b, c_: None, self.config)
                        generateFiles(self.world, datapack, self.datapackName)
                        self.assertMcTestSuccess(datapack)
                    except McScriptException as e:
                        rcon.send(
                            f'tellraw @a ["", {{"color": "red", "text": "failed to compile test {i}. '
                            f'Reason: "}}]'
                        )
                        for line in str(e).split("\n"):
                            rcon.send(f'tellraw @a ["", {{"color": "red", "text": "{line}"}}]')
                        raise e
        # noinspection PyUnresolvedReferences
        rcon.send((TELLRAW_SUCCESS if self._outcome.success else TELLRAW_FAILURE).strip())

    def assertMcTestSuccess(self, pack):
        rcon.send("reload")
        result = rcon.send(f"data get storage {self.config.NAME}:main state.vars.testResult")
        result = result.split(": ")[-1]
        self.assertEqual(result, "1", str(pack.getMainDirectory().getPath("functions").fileStructure).strip())
