import pickle
from collections.abc import Callable, Iterator, MutableMapping
from dataclasses import dataclass, field
from functools import cached_property
from itertools import chain
from pathlib import Path
from threading import RLock
from types import GenericAlias, TracebackType
from typing import Generic, Iterable, Optional, ParamSpec, Self, Type, TypeVar, cast

from . import PYCONLANG_PATH
from .checksum import checksum

CACHE_PATH = PYCONLANG_PATH / "cache"

_C = TypeVar("_C")
_T = TypeVar("_T")
_K = TypeVar("_K")
_V = TypeVar("_V")
_P = ParamSpec("_P")

Glob = tuple[Path, str]

AnyPath = Path | Glob | str


def resolve_any_path(path: AnyPath) -> Iterable[Path]:
    match path:
        case Path():
            return (path,)
        case str():
            return Path().glob(path)
        case _:
            parent, pattern = path
            return parent.glob(pattern)


class _NotFound:
    pass


@dataclass
class PathCachedFunc(Generic[_P, _T]):
    paths: list[AnyPath]
    func: Callable[_P, _T]
    st_mtimes: dict[Path, float] | None = field(default=None)
    checksums: dict[Path, bytes] | None = field(default=None)
    value: _T | type[_NotFound] = field(default=_NotFound)
    lock: RLock = field(default_factory=RLock, init=False)

    def all_paths(self) -> list[Path]:
        return list(chain(*(resolve_any_path(path) for path in self.paths)))

    def up_to_date(self) -> bool:
        if self.checksums is None or self.st_mtimes is None:
            return False

        modified = [
            path
            for path in self.all_paths()
            if self.st_mtimes.get(path, 0) < path.stat().st_mtime
        ]

        for path in modified:
            if self.checksums.get(path) != checksum(path):
                return False

        return True

    def update(self) -> None:
        paths = self.all_paths()
        self.st_mtimes = {path: path.stat().st_mtime for path in paths}
        self.checksums = {path: checksum(path) for path in paths}

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
    paths: list[AnyPath]
    func: Callable[[_C], _T]
    attrname: str | None

    @cached_property
    def lock(self) -> RLock:
        return RLock()

    def __init__(self, paths: list[AnyPath], func: Callable[[_C], _T]) -> None:
        self.paths = paths
        self.func = func
        self.attrname = None
        self.__doc__ = func.__doc__

    def __set_name__(self, owner: _C, name: str) -> None:
        if self.attrname is None:
            self.attrname = name
        elif name != self.attrname:
            raise TypeError(
                "Cannot assign the same cached_property to two different names "
                f"({self.attrname!r} and {name!r})."
            )

    @cached_property
    def hidden_name(self) -> str:
        return f"__path_cached_func_{self.attrname}"

    def __get__(self, instance: _C | None, owner: type[_C] | None = None) -> _T:
        assert instance is not None

        if self.attrname is None:
            raise TypeError(
                "Cannot use cached_property instance without calling __set_name__ on it."
            )
        try:
            cache = instance.__dict__
        except (
            AttributeError
        ):  # not all objects have __dict__ (e.g. class defines slots)
            msg = (
                f"No '__dict__' attribute on {type(instance).__name__!r} "
                f"instance to cache {self.attrname!r} property."
            )
            raise TypeError(msg) from None

        val = cache.get(self.hidden_name, _NotFound)

        if val is _NotFound:
            with self.lock:
                # check if another thread filled cache while we awaited lock
                val = cache.get(self.hidden_name, _NotFound)
                if val is _NotFound:
                    val = PathCachedFunc(self.paths, self.func)
                    try:
                        cache[self.hidden_name] = val
                    except TypeError:
                        msg = (
                            f"The '__dict__' attribute on {type(instance).__name__!r} instance "
                            f"does not support item assignment for caching {self.attrname!r} property."
                        )
                        raise TypeError(msg) from None
        return cast(_T, val(instance))

    __class_getitem__ = classmethod(GenericAlias)


def path_cached_property(
    *paths: AnyPath,
) -> Callable[[Callable[[_C], _T]], PathCachedProperty[_C, _T]]:
    def wrap(func: Callable[[_C], _T]) -> PathCachedProperty[_C, _T]:
        return PathCachedProperty(list(paths), func)

    return wrap


@dataclass
class PersistentDict(Generic[_K, _V], MutableMapping[_K, _V]):
    name: str
    paths: list[AnyPath]

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

    def __delitem__(self, key: _K) -> None:
        del self.value[key]

    def __len__(self) -> int:
        return len(self.value)

    def __iter__(self) -> Iterator[_K]:
        return iter(self.value)

    def __contains__(self, item: object) -> bool:
        return item in self.value

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> bool:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_bytes(
            pickle.dumps((self.value, self.func.st_mtimes, self.func.checksums))
        )
        return True
