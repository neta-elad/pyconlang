from collections.abc import Callable
from multiprocessing import RLock
from pathlib import Path
from types import GenericAlias
from typing import Generic, TypeVar, cast

from pyconlang.checksum import checksum

_C = TypeVar("_C")
_T = TypeVar("_T")


class _NotFound:
    pass


class PathCachedProperty(Generic[_C, _T]):
    paths: list[Path]
    func: Callable[[_C], _T]
    st_mtimes: list[float] | None
    checksums: list[bytes] | None
    value: _T | type[_NotFound]

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

    def __init__(self, paths: list[Path], func: Callable[[_C], _T]) -> None:
        self.paths = paths
        self.func = func
        self.checksums = None
        self.st_mtimes = None
        self.value = _NotFound
        self.lock = RLock()
        self.__doc__ = func.__doc__

    def __get__(self, instance: _C | None, owner: type[_C] | None = None) -> _T:
        assert instance is not None

        if not self.up_to_date():
            with self.lock:
                if not self.up_to_date():
                    self.update()
                    self.value = self.func(instance)

        assert self.checksums is not None
        assert self.value is not _NotFound

        return cast(_T, self.value)

    def __del__(self) -> None:
        pass  # called second

    __class_getitem__ = classmethod(GenericAlias)


def path_cached_property(
    *paths: Path,
) -> Callable[[Callable[[_C], _T]], PathCachedProperty[_C, _T]]:
    def wrap(func: Callable[[_C], _T]) -> PathCachedProperty[_C, _T]:
        return PathCachedProperty(list(paths), func)

    return wrap
