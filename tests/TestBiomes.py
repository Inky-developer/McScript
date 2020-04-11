import unittest

from mcscript.data.Config import Config
from mcscript.data.minecraftData import biomes


class TestBiomes(unittest.TestCase):
    def setUp(self) -> None:
        self.config = Config("config.ini")

    def test_biomes(self):
        biomes.assertLoaded()
        self.assertTrue(len(biomes.BIOMES) > 0)


if __name__ == '__main__':
    unittest.main()
