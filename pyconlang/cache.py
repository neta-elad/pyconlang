import pickle
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import cached_property
from multiprocessing import RLock
from multiprocessing.synchronize import RLock as RLockClass
from pathlib import Path
from types import GenericAlias
from typing import Generic, ParamSpec, TypeVar, cast

from . import PYCONLANG_PATH
from .checksum import checksum

CACHE_PATH = PYCONLANG_PATH / "cache"

_C = TypeVar("_C")
_T = TypeVar("_T")
_K = TypeVar("_K")
_V = TypeVar("_V")
_P = ParamSpec("_P")


class _NotFound:
    pass


@dataclass
class PathCachedFunc(Generic[_P, _T]):
    paths: list[Path]
    func: Callable[_P, _T]
    st_mtimes: list[float] | None = field(default=None)
    checksums: list[bytes] | None = field(default=None)
    value: _T | type[_NotFound] = field(default=_NotFound)
    lock: RLockClass = field(default_factory=RLock, init=False)

    def up_to_date(self) -> bool:
        if self.checksums is None or self.st_mtimes is None:
            return False

        modified = [
            path
            for st_mtime, path in zip(self.st_mtimes, self.paths)
            if st_mtime < path.stat().st_mtime
        ]

        for cached_checksum, path in zip(self.checksums, modified):
            if cached_checksum != checksum(path):
                return False

        return True

    def update(self) -> None:
        self.st_mtimes = [path.stat().st_mtime for path in self.paths]
        self.checksums = [checksum(path) for path in self.paths]

    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> _T:
        if not self.up_to_date():
            with self.lock:
                if not self.up_to_date():
                    self.update()
                    self.value = self.func(*args, **kwargs)

        assert self.checksums is not None
        assert self.value is not _NotFound

        return cast(_T, self.value)


class PathCachedProperty(Generic[_C, _T]):
    func: PathCachedFunc[[_C], _T]

    def __init__(self, paths: list[Path], func: Callable[[_C], _T]) -> None:
        self.func = PathCachedFunc(paths, func)
        self.__doc__ = func.__doc__

    def __get__(self, instance: _C | None, owner: type[_C] | None = None) -> _T:
        assert instance is not None
        return self.func(instance)

    __class_getitem__ = classmethod(GenericAlias)


def path_cached_property(
    *paths: Path,
) -> Callable[[Callable[[_C], _T]], PathCachedProperty[_C, _T]]:
    def wrap(func: Callable[[_C], _T]) -> PathCachedProperty[_C, _T]:
        return PathCachedProperty(list(paths), func)

    return wrap


@dataclass
class PersistentDict(Generic[_K, _V]):
    name: str
    paths: list[Path]

    @cached_property
    def cache_path(self) -> Path:
        return (CACHE_PATH / self.name).with_suffix(".cache")

    @cached_property
    def func(self) -> PathCachedFunc[[], dict[_K, _V]]:
        if not self.cache_path.exists():
            return PathCachedFunc(self.paths, dict)

        value, st_times, checksums = pickle.loads(self.cache_path.read_bytes())

        return PathCachedFunc(self.paths, dict, st_times, checksums, value)

    @property
    def value(self) -> dict[_K, _V]:
        return self.func()

    def __getitem__(self, item: _K) -> _V:
        return self.value[item]

    def __setitem__(self, key: _K, value: _V) -> None:
        self.value[key] = value

    def __contains__(self, item: _K) -> bool:
        return item in self.value

    def __del__(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_bytes(
            pickle.dumps((self.value, self.func.st_mtimes, self.func.checksums))
        )
