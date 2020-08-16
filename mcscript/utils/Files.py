from io import StringIO
from typing import Dict, Optional


class Files:
    """
    Simple list of `io.StringIo`'s for in-memory file management.

    >>> f = Files()
    >>> file = f.push("foo")
    >>> _ = file.write("content")
    >>> f.get().getvalue()
    'content'
    >>> f["foo"].getvalue()
    'content'
    """

    def __init__(self):
        self.files: Dict[str, StringIO] = {}
        self.current = None

    def push(self, f_name: str) -> StringIO:
        if f_name in self.files:
            raise ValueError(f"File '{f_name}' already exists!")

        io = StringIO()
        self.files[f_name] = io
        self.current = io
        return io

    def get(self) -> Optional[StringIO]:
        return self.current

    def __getitem__(self, item) -> StringIO:
        return self.files[item]

    def __iter__(self):
        return iter(self.files)

    # Debug representation
    def __str__(self):
        return "\n===\n".join(f"{name}\n{len(name) * '-'}\n{self.files[name].getvalue()}" for name in self.files)
