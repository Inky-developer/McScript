from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import List, Literal, TYPE_CHECKING

from lark import LarkError

from mcscript.data.selector import selectorGrammar
from mcscript.data.selector.selectorData import (
    getByName, getSelectors, Integer, Nbt, Range, Repeat, SelectorArgument,
    String,
)
from mcscript.exceptions.compileExceptions import McScriptInvalidSelectorError

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


@dataclass()
class Selector:
    selector: Literal["p", "a", "r", "s", "e"]
    arguments: List[SelectorArgument]

    def sort(self):
        """
        Sorts the arguments to match the specified priority values for the best performance in minecraft

        Returns:
            None
        """

        def get_priority(x: SelectorArgument) -> int:
            if x.negative:
                return x.selector.priority[1]
            return x.selector.priority[0]

        self.arguments.sort(key=get_priority, reverse=True)

    def verify(self, compileState: CompileState):
        """
        Verifies that the selector is specified correctly. Raises an error if not.

        Args:
            compileState: the compile state

        Returns:
            None
        """
        forbidden = []
        if self.selector in ("p", "a", "r"):
            # the type may not be specified because it is already set to player
            forbidden.append("type")

        if self.selector in ("p", "r", "s"):
            # the limit is already one
            forbidden.append("limit")
            forbidden.append("sort")

        used_arguments = set()

        # repeat zero or once means at most one positive
        used_argument_selectors = {}

        for argument in self.arguments:
            if argument.selector.name in forbidden:
                raise McScriptInvalidSelectorError(
                    f"May not use argument '{argument.selector.name}' "
                    f"which is already specified by the selector @{self.selector}",
                    compileState
                )
            if argument in used_arguments:
                raise McScriptInvalidSelectorError(
                    f"Argument '{argument.selector.name}' specified twice with the same value",
                    compileState
                )
            if argument.selector in used_argument_selectors and argument.selector.repeat == Repeat.ZERO_OR_ONCE:
                if used_argument_selectors[argument.selector] is True or (
                        used_argument_selectors[argument.selector] is False and not argument.negative):
                    raise McScriptInvalidSelectorError(
                        f"Argument '{argument.selector.name}' can be used at most once",
                        compileState
                    )

            if not argument.selector.accepts.matches(argument.value):
                raise McScriptInvalidSelectorError(
                    f"Invalid type '{type(argument.value).__name__}' for argument '{argument.selector.name}': "
                    f"Expected '{argument.selector.accepts.class_representation()}'",
                    compileState
                )

            used_arguments.add(argument)

            used_argument_selectors[argument.selector] = used_argument_selectors.get(argument,
                                                                                     False) or not argument.negative

    @classmethod
    @lru_cache(maxsize=32)
    def from_string(cls, _selector: str, compileState: CompileState = None) -> Selector:
        """
        Creates a Selector from a string
        format: @[parse][key=value,...] where value has balanced parentheses

        Args:
            _selector: the selector string
            compileState: the compile state or none if not available

        Returns:
            A selector
        """
        try:
            ast = selectorGrammar.parse(_selector)
        except LarkError as e:
            raise McScriptInvalidSelectorError(
                f"Failed to parse selector '{_selector}'\n"
                f"Got Error: {e}",
                compileState
            )
        selector, *arguments = ast.children
        arguments = arguments[0].children if arguments else []

        selectorArgs = []
        for argument in arguments:
            key, value = argument.children
            value, = value.children
            negate = argument.data == "neg"

            if value.data == "number":
                value = Integer(int(value.children[0]))
            elif value.data == "range":
                min_, max_ = value.children
                value = Range(int(min_), int(max_))
            elif value.data == "range_no_max":
                _min, = value.children
                value = Range(int(_min), None)
            elif value.data == "range_no_min":
                _max, = value.children
                value = Range(None, int(_max))
            elif value.data == "string":
                value = String(value.children[0])
            elif value.data == "nbt":
                value = Nbt(_selector[value.column - 1:value.end_column - 1])
            else:
                raise ValueError(f"Don't know what to do with node {value.data}")

            try:
                selectorArgs.append(SelectorArgument(getByName(key), value, negate))
            except ValueError:
                msg = f"Invalid Selector argument: '{key}'. Must be one of:\n" \
                      f"{', '.join(i.name for i in getSelectors())}"
                if compileState is not None:
                    raise McScriptInvalidSelectorError(msg, compileState)
                else:
                    raise ValueError(msg)
        # noinspection PyTypeChecker
        return Selector(str(selector.children[0]), selectorArgs)

    def __str__(self):
        arguments = ",".join(str(i) for i in self.arguments)
        arguments = f"[{arguments}]" if self.arguments else ""
        return f"@{self.selector}{arguments}"
