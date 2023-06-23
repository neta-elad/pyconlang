from dataclasses import dataclass, field
from multiprocessing import Process, Value
from pathlib import Path
from typing import Protocol, cast

from pyconlang.cache import PersistentDict, path_cached_property


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


class SettableInt(Protocol):
    value: int


def run_test(name: str, paths: list[Path], run: int, return_value: SettableInt) -> None:
    with cast(PersistentDict[str, int], PersistentDict(name, paths)) as my_dict:
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
