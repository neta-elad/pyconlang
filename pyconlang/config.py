from dataclasses import asdict, dataclass, field
from functools import cache
from pathlib import Path
from typing import Any, Self

import toml

CONFIG_PATH = Path("pyconlang.toml")


@dataclass
class Config:
    name: str = field(default="")
    author: str = field(default="")
    syllables: bool = field(default=False)
    scope: str = field(default="")

    @classmethod
    def from_file(cls, path: Path = CONFIG_PATH) -> Self:
        return cls(**toml.loads(path.read_text()))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def save(self, path: Path = CONFIG_PATH, overwrite: bool = True) -> None:
        if path.exists() and not overwrite:
            return
        path.write_text(toml.dumps(self.to_dict()))


@cache
def config() -> Config:
    return Config.from_file()
