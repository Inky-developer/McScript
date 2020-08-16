from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Union

from lark import Token, Tree


class SourceAnnotationList:
    def __init__(self, *source_annotations: SourceAnnotation):
        self.source_annotations = list(source_annotations)

    def append(self, sourceAnnotation: SourceAnnotation):
        self.source_annotations.append(sourceAnnotation)

    def sorted(self) -> SourceAnnotationList:
        """
        Sorts by line numbers in place
        """
        # noinspection PyTypeChecker
        return SourceAnnotationList(*sorted(self.source_annotations))

    def __add__(self, other) -> SourceAnnotationList:
        if isinstance(other, SourceAnnotation):
            return SourceAnnotationList(*self.source_annotations, other)

        if isinstance(other, SourceAnnotationList):
            return SourceAnnotationList(*self.source_annotations, *other.source_annotations)

        return NotImplemented

    def __radd__(self, other) -> SourceAnnotationList:
        if isinstance(other, SourceAnnotation):
            return SourceAnnotationList(other, *self.source_annotations)

        return NotImplemented

    def __iadd__(self, other) -> SourceAnnotationList:
        if isinstance(other, SourceAnnotation):
            self.append(other)
            return self

        if isinstance(other, SourceAnnotationList):
            for source_annotation in other.source_annotations:
                self.append(source_annotation)
            return self

        return NotImplemented

    def __str__(self):
        return "\n".join(str(i) for i in self.source_annotations)


@dataclass(order=True)
class SourceAnnotation:
    """ Used in Error or Warning messages to describe what is happening at a specific line of code"""
    code: List[str] = field(compare=False)
    line: int
    column: int
    end_line: int
    end_column: int
    annotation: str = field(compare=False)
    line_format: str = field(default="{line} | {message}", compare=False)

    @classmethod
    def from_token(cls, source_code: List[str], token_or_tree: Union[Token, Tree], annotation: str) -> SourceAnnotation:
        return SourceAnnotation(
            source_code,
            token_or_tree.line - 1,
            token_or_tree.column - 1,
            token_or_tree.end_line - 1,
            token_or_tree.end_column - 1,
            str(annotation)
        )

    def line_number_padding(self, number: int = None) -> str:
        """ indents a line number to be consistent with the largest possible line number"""
        max_size = len(str(len(self.code)))

        if number is not None:
            return str(number).rjust(max_size, " ")
        return "".rjust(max_size, " ")

    def __add__(self, other) -> SourceAnnotationList:
        if isinstance(other, SourceAnnotation):
            return SourceAnnotationList(self, other)

        return NotImplemented

    def __str__(self):
        """
        Converts to a string of this format:
        <line> | <source code>
                    ^^^^ <description of what is happening at this point>
        """

        str_code = self.line_format.format(
            line=self.line_number_padding(self.line + 1),
            message=self.code[self.line]
        )

        column_range = self.end_column - self.column if self.line == self.end_line \
            else len(self.code[self.line]) - self.column

        first_line, *message_lines = [i for i in self.annotation.split("\n")]

        message = [self.line_format.format(
            line=self.line_number_padding(),
            message=f"{'':>{self.column}}{'^' * column_range} {first_line}"
        )]

        for line in message_lines:
            message.append(self.line_format.format(
                line=self.line_number_padding(),
                message=f"{'':>{self.column + column_range}} {line}"
            ))
        message = "\n".join(message)

        return f"{str_code}\n" \
               f"{message}"
