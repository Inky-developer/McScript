from typing import List

from mcscript.compiler.Context import Context


class ContextStack:
    def __init__(self):
        self.stack: List[Context] = []
        self.data: List[Context] = []

    def append(self, context: Context):
        self.stack.append(context)
        self.data.append(context)

    def index(self) -> int:
        return max(len(self.data) - 1, 0)

    def tail(self) -> Context:
        return self.stack[-1]

    def getByIndex(self, index: int) -> Context:
        """ adds one to the index because the first context is reserved for built-in data"""
        return self.data[index + 1]

    def pop(self):
        self.stack.pop()

    def remove(self, context: Context) -> bool:
        while self.data.pop() != context:
            if not self.data:
                return False
        return True
