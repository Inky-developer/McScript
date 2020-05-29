import pkgutil

# import all submodules so that all function get registered
from importlib import import_module


def iterBuiltins():
    for importer, modname, ispkg in pkgutil.walk_packages(__path__):
        yield modname


for name in iterBuiltins():
    import_module("." + name, __name__)
