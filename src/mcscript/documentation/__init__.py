import json

from src.mcscript.data import Config
from src.mcscript.documentation import builtinEnumGenerator, builtinFunctionGenerator

if __name__ == '__main__':
    config = Config()
    print(json.dumps(builtinFunctionGenerator.generate(config)))
    print(json.dumps(builtinEnumGenerator.generate(config)))
