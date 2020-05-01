from typing import List, Union

from lark import Token, Tree


def textLocation(code: List[str], tokenOrTree: Union[Tree, Token], description: str = "") -> str:
    lineWidth = len(str(len(code)))
    line = tokenOrTree.line
    end_line = tokenOrTree.end_line
    column = tokenOrTree.column
    end_column = tokenOrTree.end_column

    start_error_code = max(column - 1, 0)
    error_code = max(end_column - column, 0) if line == end_line else len(
        code) - start_error_code

    lineIndent = f"{line:>{lineWidth}} |     "
    indent = f"{' ' * lineWidth} |     "

    text = f"{lineIndent}{code[line - 1]}\n" \
           f"{indent}{' ' * start_error_code}{'^' * error_code}"

    if description:
        line, *lines = description.split("\n")

        linesToAdd = [f" {line}"]

        for line in lines:
            linesToAdd.append(f"{indent}{' ' * (start_error_code + error_code)} {line}")

        text += "\n".join(linesToAdd)

    return text
