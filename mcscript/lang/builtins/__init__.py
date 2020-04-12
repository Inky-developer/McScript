import pkgutil

# import all submodules so that all function get registered
from importlib import import_module


def iterBuiltins():
    for importer, modname, ispkg in pkgutil.walk_packages(__path__):
        yield modname


for modname in iterBuiltins():
    import_module("." + modname, __name__)
