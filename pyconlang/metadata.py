from dataclasses import asdict, dataclass, field
from functools import cache
from pathlib import Path
from typing import Any, Dict

import toml

METADATA_PATH = Path("metadata.toml")


@dataclass
class Metadata:
    name: str = field(default="")
    author: str = field(default="")
    syllables: bool = field(default=False)

    @classmethod
    def from_file(cls, path: Path = METADATA_PATH) -> "Metadata":
        return cls(**toml.loads(path.read_text()))

    @classmethod
    @cache
    def default(cls) -> "Metadata":
        return cls.from_file()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def save(self, path: Path = METADATA_PATH, overwrite: bool = True) -> None:
        if path.exists() and not overwrite:
            return
        path.write_text(toml.dumps(self.to_dict()))
