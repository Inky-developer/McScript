from src.mcscript.utils.NamespaceBase import NamespaceBase


class Namespace(NamespaceBase):
    def set(self, variable, value):
        if self.predecessor and variable in self.predecessor:
            self.predecessor.set(variable, value)
        else:
            self.namespace[variable] = value

    def get(self, variable):
        if variable in self.namespace:
            return self.namespace[variable]
        if self.predecessor:
            return self.predecessor.get(variable)
        raise ValueError("Unknown variable: " + variable)

    def __delitem__(self, item):
        del self.namespace[item]
