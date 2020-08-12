from typing import List, Optional

from mcscript.compiler.Context import Context


class ContextStack:
    def __init__(self):
        self.stack: List[Context] = []
        self.data: List[Context] = []

    def append(self, context: Context):
        self.stack.append(context)
        self.data.append(context)

    def index(self) -> int:
        return len(self.data)

    def search_by_pos(self, line: int, column: int) -> Optional[Context]:
        """
        Searches the stack for a context defined at `line` and `column`

        Args:
            line: the line
            column: the column

        Returns:
            The matching context, if found
        """
        for context in self.stack:
            if context.definition == (line, column):
                return context

        return None

    def tail(self) -> Context:
        return self.stack[-1]

    def pop(self):
        self.stack.pop()

    def remove(self, context: Context) -> bool:
        while self.data.pop() != context:
            if not self.data:
                return False
        return True
