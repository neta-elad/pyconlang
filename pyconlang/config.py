from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import asdict, dataclass, fields, replace
from functools import cache, wraps
from pathlib import Path
from typing import Any, ParamSpec, Self, TypeVar

import toml

_P = ParamSpec("_P")
_T = TypeVar("_T")

CONFIG_PATH = Path("pyconlang.toml")


@dataclass
class Config:
    name: str = ""
    author: str = ""
    syllables: bool = False
    scope: str = ""

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
    return Config()


@contextmanager
def config_as(new_config: Config) -> Generator[Config, None, None]:
    original_config = replace(config())
    update_config(new_config)
    try:
        yield new_config
    finally:
        update_config(original_config)


@contextmanager
def file_config() -> Generator[Config, None, None]:
    with config_as(Config.from_file()) as new_config:
        yield new_config


def with_file_config(func: Callable[_P, _T]) -> Callable[_P, _T]:
    @wraps(func)
    def wrapped(*args: _P.args, **kwargs: _P.kwargs) -> _T:
        with file_config():
            return func(*args, **kwargs)

    return wrapped


@contextmanager
def config_scope_as(scope: str) -> Generator[Config, None, None]:
    with config_as(replace(config(), scope=scope)) as new_config:
        yield new_config


def update_config(new_config: Config) -> None:
    for field in fields(Config):
        setattr(config(), field.name, getattr(new_config, field.name))
