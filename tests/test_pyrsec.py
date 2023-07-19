import pytest

from pyconlang.pyrsec import Failure, PyrsecError, Success, lift2, regex, string, token


def test_string() -> None:
    plus = string("+")

    assert plus.parse("+") == Success(1, "+")
    assert plus.parse("+-") == Success(1, "+")
    assert plus.parse("-") == Failure(0, "+")

    longer = string("longer")

    assert longer.parse("longer") == Success(6, "longer")

    with pytest.raises(PyrsecError):
        longer.parse_or_raise("short")


def test_regex() -> None:
    number = regex(r"[1-9][0-9]*")

    assert number.parse("123") == Success(3, "123")
    assert number.parse("103") == Success(3, "103")
    assert number.parse("03") == Failure(0, r"[1-9][0-9]*")


def test_compose() -> None:
    def add(x: int, y: int) -> int:
        return x + y

    number = regex(r"[1-9][0-9]*")[int]
    plus = token(string("+"))
    addition = (number << plus & number)[lift2(add)]

    assert addition.parse("123+456") == Success(7, 579)
    assert addition.parse("123 + 456") == Success(9, 579)


def test_many() -> None:
    number = token(regex(r"[1-9][0-9]*"))[int]
    numbers = ~number

    assert numbers.parse("123 456 789") == Success(11, [123, 456, 789])