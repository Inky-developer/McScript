from __future__ import annotations

from collections import Iterable
from enum import Enum
from inspect import isclass
from typing import TYPE_CHECKING, Tuple, Union

from mcscript.data.Config import Config
from mcscript.utils.CommandFormatter import CommandFormatter

if TYPE_CHECKING:
    from mcscript.lang.resource.BooleanResource import BooleanResource
    from mcscript.compiler.CompileState import CompileState


class Storage(Enum):
    NAME = "main"
    VARS = "state.vars"
    TEMP = "state.tempVal"

    def __str__(self):
        return self.value


class Type(Enum):
    BYTE = "byte"
    DOUBLE = "double"
    FLOAT = "float"
    INT = "int"
    LONG = "long"
    SHORT = "short"

    def __str__(self):
        return self.value


class StringEnum(Enum):
    def __call__(self, **kwargs):
        return stringFormat(self.value, **kwargs)


class Selector(StringEnum):
    CURRENT_ENTITY = "@s{filter}"
    ALL_PLAYERS = "@a{filter}"
    NEAREST_PLAYER = "@p{filter}"
    ALL_ENTITIES = "@e{filter}"
    RANDOM_PLAYER = "@r{filter}"

    def filter(self, **kwargs) -> str:
        ret = []
        for key in kwargs:
            ret.append(f"{key}={kwargs[key]}")
        return self(filter=f"[{','.join(ret)}]")


class Struct(StringEnum):
    VAR = '{{"{var}":{value}}}'

    @classmethod
    def ARRAY(cls, *values):
        if len(values) == 1 and isinstance(values[0], Iterable):
            values = list(values[0])
        return f"[{','.join(str(value) for value in values)}]" if values else '[""]'

    @classmethod
    def fromDict(cls, dictionary: dict) -> str:
        result = []
        for key in dictionary:
            result.append(f"{key}={dictionary[key]}")
        return f'{{{", ".join(result)}}}'


class ExecuteCommand(StringEnum):
    """ Allows to create an execute command"""
    AS = "as {target} {command}"
    AT = "at {target} {command}"
    POSITIONED = "positioned {x} {y} {z} {command}"
    IF_SCORE_RANGE = "if score {stack} {name} matches {range} {command}"
    IF_SCORE = "if score {stack} {name} {relation} {stack2} {name2} {command}"
    UNLESS_SCORE = "unless score {stack} {name} {relation} {stack2} {name2} {command}"
    UNLESS_SCORE_RANGE = "unless score {stack} {name} matches {range} {command}"
    IF_BLOCK = "if block {x:~} {y:~} {z:~} {block} {command}"
    IF_ENTITY = "if entity {target} {command}"
    IF_PREDICATE = "if predicate {:Config.currentConfig.UTILS}:{predicate} {command}"


class ConditionalExecute:
    """
    Can be called with a command that will only execute if a predefined condition evaluates to True.
    it also supports static conditions which can either be true or false. If true, the command will always be run.
    If false, the command will never be run.
    """

    def __init__(self, condition: Union[str, bool]):
        self.condition = condition
        self.isStatic = isinstance(self.condition, bool)

    def toResource(self, compileState) -> BooleanResource:
        """
        Converts this to a boolean resource.

        Args:
            compileState: the compile state

        Returns:
            a boolean resource
        """
        from mcscript.lang.resource.BooleanResource import BooleanResource
        if self.isStatic:
            return BooleanResource(self.condition, True)

        stack = compileState.expressionStack.next()
        compileState.writeline(Command.SET_VALUE(
            stack=stack,
            value=0
        ))
        compileState.writeline(self(Command.SET_VALUE(
            stack=stack,
            value=1
        )))
        return BooleanResource(stack, False)

    def if_else(self, compileState: CompileState) -> Tuple[ConditionalExecute, ConditionalExecute]:
        """
        Simplifies it's own conditions to be a simple boolean check and returns one condition that runs
        if the original condition evaluates to True and one condition that runs if the original condition
        evaluates to false

        Args:
            compileState: the compile state

        Returns:
            Another ConditionalExecute with a simpler condition
        """
        boolean = self.toResource(compileState)
        if boolean.isStatic:
            return ConditionalExecute(boolean.value), ConditionalExecute(not boolean.value)

        return (
            ConditionalExecute(Command.EXECUTE(
                sub=ExecuteCommand.IF_SCORE_RANGE(stack=boolean.value, range=1)
            )),
            ConditionalExecute(Command.EXECUTE(
                sub=ExecuteCommand.UNLESS_SCORE_RANGE(stack=boolean.value, range=1)
            ))
        )

    def __call__(self, command: str) -> str:
        if self.isStatic:
            return command if self.condition else ""
        return f"{self.condition}{command}"

    def __repr__(self):
        return f"ConditionalExpression({self.condition})"


class Relation(StringEnum):
    EQUAL = "=", lambda a, b: a == b, lambda v: f"{v}"
    NOT_EQUAL = "!=", lambda a, b: a != b, lambda v: f"{v}"
    GREATER = ">", lambda a, b: a > b, lambda v: f"{v + 1}.."
    GREATER_OR_EQUAL = ">=", lambda a, b: a >= b, lambda v: f"{v}.."
    LESS = "<", lambda a, b: a < b, lambda v: f"..{v - 1}"
    LESS_OR_EQUAL = "<=", lambda a, b: a <= b, lambda v: f"..{v}"

    def __new__(cls, value, func, getRange):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.testRelation = func
        obj.getRange = getRange
        return obj

    def swap(self) -> Relation:
        """
        swaps both values and returns the relation that is required to keep the value.

        Examples:
            a == b (=) b == a => Relation.EQUAL == Relation.EQUAL.swap()

            a <= b (=) b >= a => Relation.GREATER_OR_EQUAL == Relation.LESS_OR_EQUAL.swap()
        """
        if self == Relation.EQUAL:
            return Relation.EQUAL
        elif self == Relation.NOT_EQUAL:
            return Relation.NOT_EQUAL
        elif self == Relation.LESS:
            return Relation.GREATER
        elif self == Relation.LESS_OR_EQUAL:
            return Relation.GREATER_OR_EQUAL
        elif self == Relation.GREATER:
            return Relation.LESS
        elif self == Relation.GREATER_OR_EQUAL:
            return Relation.LESS_OR_EQUAL
        raise ValueError("What am I?")

    @classmethod
    def get(cls, string):
        """ In the grammar relations have the format VERIFY_..."""
        return cls[string.split("VERIFY_")[-1]]


class BinaryOperator(StringEnum):
    PLUS = "+"
    MINUS = "-"
    TIMES = "*"
    DIVIDE = "/"
    MODULO = "%"


class UnaryOperator(StringEnum):
    MINUS = "-"
    INCREMENT_ONE = "++"
    DECREMENT_ONE = "--"


class Command(StringEnum):
    # sets a value to a scoreboard stack
    SET_VALUE = "scoreboard players set {stack} {name} {value}"
    SET_VALUE_EQUAL = "scoreboard players operation {stack} {name} = {stack2} {name2}"
    # return a value from a scoreboard
    GET_SCOREBOARD_VALUE = "scoreboard players get {stack} {name}"

    # Does a binary operation with two scoreboard values
    OPERATION = "scoreboard players operation {stack} {name} {operator}= {stack2} {name2}"
    # simpler than OPERATION, can only add values
    ADD_SCORE = "scoreboard players add {stack} {name} {value}"
    REMOVE_SCORE = "scoreboard players remove {stack} {name} {value}"

    # loads a variable from storage to a scoreboard
    LOAD_SCORE = "execute store result score {stack} {name} run " \
                 "data get storage {name2}:{:Storage.NAME} {:Storage.VARS}.{var} {scale:1}"
    LOAD_SCORE_NO_SCALE = "execute store result score {stack} {name} run " \
                          "data get storage {name2}:{:Storage.NAME} {:Storage.VARS}.{var}"

    # sets a variable to a value
    SET_VARIABLE = "data modify storage {name}:{:Storage.NAME} {:Storage.VARS}.{address} merge value {struct}"
    SET_VARIABLE_VALUE = "data modify storage {name}:{:Storage.NAME} {:Storage.VARS}.{address} set value {value}"

    COPY_VARIABLE = "data modify storage {name}:{:Storage.NAME} {:Storage.VARS}.{address} " \
                    "set from storage {name}:{:Storage.NAME} {:Storage.VARS}.{address2}"
    REMOVE_VARIABLE = "data remove storage {name}:{:Storage.NAME} {:Storage.VARS}.{address}"

    # loads the result of another command as int into a storage
    SET_VARIABLE_FROM = \
        "execute store result storage {name}:{:Storage.NAME} " \
        "{:Storage.VARS}.{var} {type:int} {scale:1} run {command}"
    SET_VALUE_FROM = "execute store result score {stack} {name} run {command}"

    # calls a function
    RUN_FUNCTION = "function {name}:{function}"

    EXECUTE = "execute {sub}run {command}"

    TELLRAW = "tellraw {target:@s} {text}"
    TITLE = "title {target:@s} title {text}"
    SUBTITLE = "title {target:@s} subtitle {text}"
    ACTIONBAR = "title {target:@s} actionbar {text}"

    SET_BLOCK = "setblock {x:~} {y:~} {z:~} {block}{blockstate}{nbt}"
    SET_BLOCK_ABS = "setblock {x:0} {y:0} {z:0} {block}{blockstate}{nbt}"

    MODIFY_BLOCK_FROM_VARIABLE = "data modify block {x:~} {y:~} {z:~} {path} set from storage " \
                                 "{name}:{:Storage.NAME} {:Storage.VARS}.{address}"

    APPEND_ARRAY = "data modify storage {name}:{:Storage.NAME} {:Storage.VARS}.{address} append value {value}"
    APPEND_ARRAY_FROM = "data modify storage {name}:{:Storage.NAME} {:Storage.VARS}.{address} append " \
                        "from storage {name}:{:Storage.NAME} {:Storage.VARS}.{address2}"
    INSERT_ARRAY = "data modify storage {name}:{:Storage.NAME} {:Storage.VARS}.{address} insert {index} value {value}"
    INSERT_ARRAY_FROM = "data modify storage {name}:{:Storage.NAME} {:Storage.VARS}.{address} insert {index} " \
                        "from storage {name}:{:Storage.NAME} {:Storage.VARS}.{address2}"

    # summons an entity
    SUMMON_ENTITY = "summon {entity} {x:~} {y:~} {z:~} {nbt}"
    KILL_ENTITY = "kill {target}"


def multiple_commands(*commands):
    return "\n".join(commands)


def stringFormat(string, **kwargs):
    kwargs.setdefault("name", Config.currentConfig.NAME)
    kwargs.setdefault("name2", Config.currentConfig.NAME)
    kwargs.setdefault("utils", Config.currentConfig.UTILS)
    kwargs.setdefault("ret", Config.currentConfig.RETURN_SCORE)
    kwargs.setdefault("block", Config.currentConfig.BLOCK_SCORE)
    return Formatter.format(string, **kwargs)


context = {name: obj for name, obj in globals().items() if isclass(obj) and issubclass(obj, Enum)}
context.update(Config=Config)
Formatter = CommandFormatter(context)
