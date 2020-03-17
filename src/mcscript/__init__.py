from importlib import resources

from lark import Lark

from . import Exceptions
from . import lang
from .compiler import CompileState
from .compiler import Compiler as _Compiler
from .pre_compiler import PreCompiler, StateTree
from .utils import FileStructure, NamespaceBase, utils, Address

Grammar = Lark(
    resources.open_text("src.mcscript", "McScript.lark").read(),
    parser="lalr",
    tree_class=StateTree,
    propagate_positions=True
)

Compiler = _Compiler(Grammar)

from .compile import compileMcScript
from src.mcscript.utils.cmdHelper import generateFiles, DebugWrite

__all__ = "Grammar", "Compiler", "CompileState", "NamespaceBase", "Address", \
          "Exceptions", "FileStructure", "utils", "PreCompiler", "lang", \
          "StateTree", "compileMcScript", "generateFiles", "DebugWrite"
