import pkgutil
# import all submodules so that all resource classes can be accessed using Resource.getResourceType
from importlib import import_module

from mcscript import Logger


def iterBuiltins():
    for importer, modname, ispkg in pkgutil.walk_packages(__path__):
        yield modname


for name in iterBuiltins():
    Logger.debug(f"[Resource] auto-importing {name}")
    import_module("." + name, __name__)
