from dataclasses import dataclass


@dataclass()
class ResourceSpecifier:
    base: str
    path: str

    def __str__(self):
        return f"{self.base}:{self.path}"
