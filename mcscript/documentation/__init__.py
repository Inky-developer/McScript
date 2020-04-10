if __name__ == '__main__':
    import json

    from mcscript.data import Config
    from mcscript.documentation import builtinEnumGenerator, builtinFunctionGenerator

    config = Config()
    print(json.dumps(builtinFunctionGenerator.generate(config)))
    print(json.dumps(builtinEnumGenerator.generate(config)))
