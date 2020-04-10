import pkgutil

# import all submodules so that all function get registered
from importlib import import_module

for importer, modname, ispkg in pkgutil.walk_packages(__path__):
    import_module("." + modname, __name__)
