import time
from collections.abc import Callable
from dataclasses import dataclass, field
from multiprocessing import RLock
from pathlib import Path
from types import GenericAlias
from typing import ClassVar, Generic, TypeVar, cast

from watchdog.events import (
    FileSystemEvent,
    FileSystemEventHandler,
    PatternMatchingEventHandler,
)
from watchdog.observers import Observer

from pyconlang.checksum import checksum

_C = TypeVar("_C")
_T = TypeVar("_T")


class _NOT_FOUND:
    pass


class Handler(PatternMatchingEventHandler):
    def __init__(self) -> None:
        super().__init__(["*"])

    def on_any_event(self, event: FileSystemEvent) -> None:
        print(f"Got event {event} at {time.time()}")


@dataclass
class AutoJoinedObserverWrapper:
    observer: Observer = field(default_factory=Observer)

    def __post_init__(self) -> None:
        self.observer.start()

    def watch(
        self,
        handler: FileSystemEventHandler,
        path: Path | str = Path("."),
        recursive: bool = True,
    ) -> None:
        self.observer.schedule(handler, str(path), recursive)

    def __del__(self) -> None:
        self.observer.stop()
        self.observer.join()


class PathCachedProperty(Generic[_C, _T]):
    paths: list[Path]
    func: Callable[[_C], _T]
    checksums: list[bytes] | None
    value: _T | type[_NOT_FOUND]

    cvar: ClassVar[AutoJoinedObserverWrapper] = AutoJoinedObserverWrapper()

    def up_to_date(self) -> bool:
        print(self.cvar)
        if self.checksums is None:
            return False

        for cached_checksum, path in zip(self.checksums, self.paths):
            if cached_checksum != checksum(path):
                return False

        return True

    def update(self) -> None:
        self.checksums = [checksum(path) for path in self.paths]

    def __init__(self, paths: list[Path], func: Callable[[_C], _T]) -> None:
        self.paths = paths
        self.func = func
        self.checksums = None
        self.value = _NOT_FOUND
        self.__doc__ = func.__doc__
        self.lock = RLock()

    def __get__(self, instance: _C | None, owner: type[_C] | None = None) -> _T:
        assert instance is not None

        if not self.up_to_date():
            with self.lock:
                if not self.up_to_date():
                    self.update()
                    self.value = self.func(instance)

        assert self.checksums is not None
        assert self.value is not _NOT_FOUND

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


def test_path_cached_property(tmpdir: Path) -> None:
    print()

    print(tmpdir)
    auto = AutoJoinedObserverWrapper()

    path_a = tmpdir / "a.txt"
    path_a.write_text("hello")

    time.sleep(0.1)

    path_a.read_text()

    auto.watch(Handler(), tmpdir)

    path_b = tmpdir / "b.txt"
    path_b.write_text("hi")

    time.sleep(0.1)  # have to sleep

    print("done")
    return

    @dataclass
    class A:
        counter: int = field(default=0)

        @path_cached_property(path_a, path_b)
        def test(self) -> int:
            self.counter += 1
            return self.counter

        def __del__(self) -> None:
            pass  # called first

    a = A()

    assert a.test == 1
    assert a.test == 1

    path_a.write_text("goodbye")

    assert a.test == 2

    path_b.write_text("ciao")

    assert a.test == 3
