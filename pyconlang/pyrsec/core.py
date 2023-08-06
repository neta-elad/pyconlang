from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Generic, TypeVar

_U = TypeVar("_U", covariant=True)
_I = TypeVar("_I", contravariant=True)

_V = TypeVar("_V", covariant=True)


@dataclass(eq=True, frozen=True)
class Success(Generic[_U]):
    index: int
    value: _U


@dataclass(eq=True, frozen=True)
class Failure:
    index: int
    expected: str


Value = Success[_U] | Failure
RawParser = Callable[[_I, int], Value[_U]]


@dataclass
class PyrsecError(Exception):
    text: Any
    index: int
    expected: str

    def location(self) -> int | tuple[int, int]:
        if isinstance(self.text, str) and self.text.count("\n") > 0:
            line, last_ln = self.text.count("\n", 0, self.index), self.text.rfind(
                "\n", 0, self.index
            )
            col = self.index - (last_ln + 1)
            return (line, col)
        else:
            return self.index

    def __str__(self) -> str:
        return f"Expected {self.expected} at {self.location()} in `{self.text}`"


class Parser(Generic[_I, _U]):
    @abstractmethod
    def __call__(self, text: _I, index: int) -> Value[_U]:
        ...

    def __rshift__(self, other: "Parser[_I, _V]") -> "Parser[_I, _V]":
        @SimpleParser
        def compose(text: _I, index: int) -> Value[_V]:
            result = self(text, index)
            match result:
                case Success():
                    return other(text, result.index)
                case Failure():
                    return result

        return compose

    def __lshift__(self, other: "Parser[_I, _V]") -> "Parser[_I, _U]":
        @SimpleParser
        def compose(text: _I, index: int) -> Value[_U]:
            result1 = self(text, index)
            match result1:
                case Success():
                    result2 = other(text, result1.index)
                    match result2:
                        case Success():
                            return Success(result2.index, result1.value)
                        case Failure():
                            return result2
                case Failure():
                    return result1

        return compose

    def __and__(self, other: "Parser[_I, _V]") -> "Parser[_I, tuple[_U, _V]]":
        @SimpleParser
        def aggregate(text: _I, index: int) -> Value[tuple[_U, _V]]:
            result1 = self(text, index)
            match result1:
                case Success():
                    result2 = other(text, result1.index)
                    match result2:
                        case Success():
                            return Success(
                                result2.index, (result1.value, result2.value)
                            )
                        case Failure():
                            return result2
                case Failure():
                    return result1

        return aggregate

    def __or__(self, other: "Parser[_I, _V]") -> "Parser[_I, _U | _V]":
        @SimpleParser
        def choice(text: _I, index: int) -> Value[_U | _V]:
            result = self(text, index)
            match result:
                case Success():
                    return result
                case Failure():
                    if result.index == index:
                        return other(text, index)
                    else:
                        return result

        return choice

    def __xor__(self, other: "Parser[_I, _V]") -> "Parser[_I, _U | _V]":
        @SimpleParser
        def try_choice(text: _I, index: int) -> Value[_U | _V]:
            result = self(text, index)
            match result:
                case Success():
                    return result
                case Failure():
                    return other(text, index)

        return try_choice

    def __pos__(self) -> "Parser[_I, _U]":
        @SimpleParser
        def lookahead(text: _I, index: int) -> Value[_U]:
            result = self(text, index)
            match result:
                case Success():
                    return Success(index, result.value)
                case Failure():
                    return Failure(index, result.expected)

        return lookahead

    def __neg__(self) -> "Parser[_I, _U | None]":
        @SimpleParser
        def optional(text: _I, index: int) -> Value[_U | None]:
            result = self(text, index)
            match result:
                case Success():
                    return result
                case Failure():
                    return Success(index, None)

        return optional

    def __invert__(self) -> "Parser[_I, list[_U]]":
        @SimpleParser
        def many(text: _I, index: int) -> Value[list[_U]]:
            current_index = index
            values: list[_U] = []
            while True:
                result = self(text, current_index)
                match result:
                    case Success():
                        values.append(result.value)
                        current_index = result.index
                    case Failure():
                        break

            return Success(current_index, values)

        return many

    def __getitem__(self, item: Callable[[_U], _V]) -> "Parser[_I, _V]":
        @SimpleParser
        def mapped(text: _I, index: int) -> Value[_V]:
            result = self(text, index)
            match result:
                case Success():
                    return Success(result.index, item(result.value))
                case Failure():
                    return result

        return mapped

    def parse(self, text: _I) -> Value[_U]:
        return self(text, 0)

    def parse_or_raise(self, text: _I) -> _U:
        value = self.parse(text)
        match value:
            case Success():
                return value.value
            case Failure():
                raise PyrsecError(text, value.index, value.expected)


@dataclass
class SimpleParser(Generic[_I, _U], Parser[_I, _U]):
    fun: RawParser[_I, _U]

    def __call__(self, text: _I, index: int) -> Value[_U]:
        return self.fun(text, index)
