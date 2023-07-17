from dataclasses import asdict, dataclass, field
from functools import cache
from pathlib import Path
from typing import Any

import toml

METADATA_PATH = Path("metadata.toml")

# todo: rename metadata and implement better


@dataclass
class Metadata:
    name: str = field(default="")
    author: str = field(default="")
    syllables: bool = field(default=False)
    lang: str | None = field(default=None)

    @classmethod
    def from_file(cls, path: Path = METADATA_PATH) -> "Metadata":
        return cls(**toml.loads(path.read_text()))

    @classmethod
    @cache
    def default(cls) -> "Metadata":
        return cls.from_file()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def save(self, path: Path = METADATA_PATH, overwrite: bool = True) -> None:
        if path.exists() and not overwrite:
            return
        path.write_text(toml.dumps(self.to_dict()))
