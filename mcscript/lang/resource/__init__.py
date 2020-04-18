import pkgutil
# import all submodules so that all resource classes can be accessed using Resource.getResourceType
from importlib import import_module

from mcscript import Logger


def iterBuiltins():
    for importer, modname, ispkg in pkgutil.walk_packages(__path__):
        yield modname


for modname in iterBuiltins():
    Logger.debug(f"[Resource] auto-importing {modname}")
    import_module("." + modname, __name__)
