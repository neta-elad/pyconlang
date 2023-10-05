from dataclasses import dataclass, field
from multiprocessing import Process, Value
from pathlib import Path
from typing import Protocol, cast

from pyconlang.cache import (
    PersistentDict,
    path_cache,
    path_cached_method,
    path_cached_property,
)


def test_path_cached_property(cd_tmp_path: Path) -> None:
    path_a = cd_tmp_path / "a.md"
    path_a.write_text("hello")
    path_b = cd_tmp_path / "b.txt"
    path_b.write_text("hi")

    @dataclass
    class A:
        counter: int = field(default=0)

        @path_cached_property("*.txt", path_a)
        def test(self) -> int:
            self.counter += 1
            return self.counter

    a1 = A()

    assert a1.test == 1
    assert a1.test == 1

    path_a.touch()

    assert a1.test == 1

    path_a.write_text("goodbye")

    assert a1.test == 2

    path_b.write_text("ciao")

    assert a1.test == 3

    a2 = A()

    assert a2.test == 1


def test_path_cached_func(cd_tmp_path: Path) -> None:
    path_a = cd_tmp_path / "a.md"
    path_a.write_text("hello")
    path_b = cd_tmp_path / "b.txt"
    path_b.write_text("hi")

    counter = {"val": 0}

    @path_cache("*.txt", path_a)
    def example(x: int) -> int:
        counter["val"] += x
        return counter["val"]

    assert example(1) == 1
    assert example(2) == 3

    path_a.touch()

    assert example(1) == 1
    assert example(2) == 3

    path_a.write_text("goodbye")

    assert example(1) == 4
    assert example(2) == 6


def test_path_cached_method(cd_tmp_path: Path) -> None:
    path_a = cd_tmp_path / "a.md"
    path_a.write_text("hello")
    path_b = cd_tmp_path / "b.txt"
    path_b.write_text("hi")

    @dataclass
    class Foo:
        counter: int = 0

        @path_cached_method("*.txt", path_a)
        def example(self, x: int) -> int:
            self.counter += x
            return self.counter

    foo = Foo()
    bar = Foo()

    assert foo.example(1) == 1
    assert foo.example(2) == 3
    assert bar.example(7) == 7
    assert bar.example(7) == 7

    path_a.touch()

    assert foo.example(1) == 1
    assert foo.example(2) == 3
    assert bar.example(7) == 7
    assert bar.example(2) == 9
    assert bar.example(2) == 9

    path_a.write_text("goodbye")

    assert foo.example(1) == 4
    assert foo.example(2) == 6
    assert bar.example(2) == 11


class SettableInt(Protocol):
    value: int


def run_test(name: str, paths: list[Path], run: int, return_value: SettableInt) -> None:
    with cast(PersistentDict[str, int], PersistentDict(name, list(paths))) as my_dict:
        assert return_value.value == 0

        if run == 0:
            my_dict["hello"] = 5
        elif run == 1:
            assert my_dict["hello"] == 5
        else:
            assert "hello" not in my_dict

        return_value.value = 1


def test_persistent_dict(tmp_pyconlang: Path) -> None:
    v: SettableInt = cast(SettableInt, Value("i", 0))
    a = tmp_pyconlang / "a.txt"
    a.write_text("hello")

    p = Process(
        target=run_test,
        args=(
            "cache",
            [a],
            0,
            v,
        ),
    )
    p.start()
    p.join()

    assert v.value == 1
    v.value = 0

    p = Process(
        target=run_test,
        args=(
            "cache",
            [a],
            1,
            v,
        ),
    )
    p.start()
    p.join()

    assert v.value == 1
    v.value = 0

    a.write_text("hi")

    p = Process(
        target=run_test,
        args=(
            "cache",
            [a],
            2,
            v,
        ),
    )
    p.start()
    p.join()

    assert v.value == 1
    v.value = 0
