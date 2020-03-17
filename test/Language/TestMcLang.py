import unittest
from os.path import join
from shutil import rmtree

from src.mcscript import compileMcScript, generateFiles
from src.mcscript.data.Config import Config
from src.mcscript.utils.cmdHelper import getWorld
from test.Language.loadScripts import loadScripts
from test.server import rcon

TELLRAW_SUCCESS = '''
/tellraw @a ["",{"text":"["},{"text":"McScript","color":"gold"},{"text":"] "},{"text":"All tests successful!","color":"green"}]
'''
TELLRAW_FAILURE = '''
/tellraw @a ["",{"text":"["},{"text":"McScript","color":"gold"},{"text":"] "},{"text":"Some test(s) failed!","color":"red"}]
'''


class TestMcLang(unittest.TestCase):
    def setUp(self) -> None:
        self.tests = loadScripts()
        self.wrapper = self.tests.pop("Wrapper")[0]
        self.world = getWorld("McScript", r"D:\Dokumente\Informatik\Python\McScript\test\server")
        self.datapackName = "McScript-tests"
        self.config = Config("config.ini")

        rmtree(
            join(self.world.getDatapackPath(), self.datapackName),
            onerror=lambda func, path, exc_info: print("Warning: Could not remove ", path, exc_info)
        )

        self.testCount = 0
        for test in self.tests:
            for _ in self.tests[test]:
                self.testCount += 1

    def tearDown(self) -> None:
        rmtree(
            join(self.world.getDatapackPath(), self.datapackName),
            onerror=lambda func, path, exc_info: print("Warning: Could not remove ", path, exc_info)
        )

    def testMcLang(self):
        i = 0
        for test in self.tests:
            for index, code in enumerate(self.tests[test]):
                i += 1
                with self.subTest(name=test, index=index):
                    code = self.wrapper.format(code, name=test, index=i, count=self.testCount)
                    datapack = compileMcScript(code, lambda a, b, c_: None, self.config)
                    generateFiles(self.world, datapack, self.datapackName)
                    self.assertMcTestSuccess(datapack)
        rcon.send((TELLRAW_SUCCESS if self._outcome.success else TELLRAW_FAILURE).strip())

    def assertMcTestSuccess(self, pack):
        rcon.send("reload")
        result = rcon.send("data get storage mcscript:main state.vars.testResult")
        result = result.split(": ")[-1]
        self.assertEqual(result, "1", str(pack.getMainDirectory().getPath("functions").fileStructure).strip())
