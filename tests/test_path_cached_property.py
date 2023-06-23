from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeVar

from pyconlang.cache import path_cached_property

_C = TypeVar("_C")
_T = TypeVar("_T")


class _NOT_FOUND:
    pass


def test_path_cached_property(tmpdir: Path) -> None:
    path_a = tmpdir / "a.txt"
    path_a.write_text("hello")
    path_b = tmpdir / "b.txt"
    path_b.write_text("hi")

    @dataclass
    class A:
        counter: int = field(default=0)

        @path_cached_property(path_a, path_b)
        def test(self) -> int:
            self.counter += 1
            return self.counter

    a = A()

    assert a.test == 1
    assert a.test == 1

    path_a.touch()

    assert a.test == 1

    path_a.write_text("goodbye")

    assert a.test == 2

    path_b.write_text("ciao")

    assert a.test == 3
