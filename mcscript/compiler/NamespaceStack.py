from mcscript.compiler.Namespace import Namespace


class NamespaceStack:
    def __init__(self):
        self.stack = []
        self.data = []

    def append(self, namespace: Namespace):
        self.stack.append(namespace)
        self.data.append(namespace)

    def index(self) -> int:
        return max(len(self.data) - 1, 0)

    def tail(self) -> Namespace:
        return self.stack[-1]

    def getByIndex(self, index: int) -> Namespace:
        return self.data[index]

    def pop(self):
        self.stack.pop()
