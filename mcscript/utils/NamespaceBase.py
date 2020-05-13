from __future__ import annotations

from typing import Dict, Iterator, Mapping, Optional, TypeVar

T = TypeVar("T")


class NamespaceBase(Mapping[str, T]):
    class NamespaceIterator(Iterator[T]):
        def __init__(self, namespace: NamespaceBase):
            self.data = iter(namespace.namespace.keys())
            self.predecessor = iter(namespace.predecessor) if namespace.predecessor is not None else None
            self.finishedBase = False

        def __next__(self) -> T:
            if not self.finishedBase:
                try:
                    return next(self.data)
                except StopIteration:
                    self.finishedBase = True
            if not self.predecessor:
                raise StopIteration
            return next(self.predecessor)

        def __iter__(self):
            return self

    def __init__(self, previous: Optional[NamespaceBase]):
        self.predecessor = previous
        self.index = previous.index + 1 if previous else 0
        self.namespace: Dict[str, T] = {}

    def setPredecessor(self, predecessor: NamespaceBase):
        self.predecessor = predecessor
        self.index = self.predecessor.index + 1

    def asDict(self):
        return {key: self[key] for key in self}

    def __iter__(self) -> Iterator[T]:
        return self.NamespaceIterator(self)

    def __len__(self) -> int:
        return len(self.namespace) + len(self.predecessor) if self.predecessor else len(self.namespace)

    def __getitem__(self, item) -> T:
        try:
            return self.namespace[item]
        except KeyError as e:
            if self.predecessor is not None:
                return self.predecessor[item]
            raise KeyError from e

    # def __delitem__(self, key):
    #     del self.namespace[str(key)]

    def __contains__(self, item):
        return item in self.namespace or self.predecessor and item in self.predecessor

    def __repr__(self):
        return f"Namespace({self.namespace}, [{repr(self.predecessor)}])"
