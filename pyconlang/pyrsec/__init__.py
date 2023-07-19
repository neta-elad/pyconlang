import re
from abc import abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Generic, TypeVar, cast

_I = TypeVar("_I", contravariant=True)
_U = TypeVar("_U", covariant=True)
_V = TypeVar("_V", covariant=True)

_T = TypeVar("_T")
_T1 = TypeVar("_T1", contravariant=True)
_T2 = TypeVar("_T2", contravariant=True)
_T3 = TypeVar("_T3", contravariant=True)
_T4 = TypeVar("_T4", contravariant=True)
_T5 = TypeVar("_T5", contravariant=True)
_T6 = TypeVar("_T6", contravariant=True)
_T7 = TypeVar("_T7", contravariant=True)


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


class PyrsecError(Exception):
    ...


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
                raise PyrsecError(value.expected)


@dataclass
class SimpleParser(Generic[_I, _U], Parser[_I, _U]):
    fun: RawParser[_I, _U]

    def __call__(self, text: _I, index: int) -> Value[_U]:
        return self.fun(text, index)


@dataclass
class ForwardParser(Parser[_I, _U]):
    parser: Parser[_I, _U] | None = field(default=None)

    def __call__(self, text: _I, index: int) -> Value[_U]:
        assert self.parser is not None  # todo: better error handling?
        return self.parser(text, index)


def fix(fun: Callable[[Parser[_I, _U]], Parser[_I, _U]]) -> Parser[_I, _U]:
    forward = cast(ForwardParser[_I, _U], ForwardParser())
    forward.parser = fun(forward)
    return forward


def lift2(fun: Callable[[_T1, _T2], _U]) -> Callable[[tuple[_T1, _T2]], _U]:
    def lifted(pair: tuple[_T1, _T2]) -> _U:
        a, b = pair
        return fun(a, b)

    return lifted


def lift3(
    fun: Callable[[_T1, _T2, _T3], _U]
) -> Callable[[tuple[tuple[_T1, _T2], _T3]], _U]:
    def lifted(triple: tuple[tuple[_T1, _T2], _T3]) -> _U:
        (a, b), c = triple
        return fun(a, b, c)

    return lifted


def lift4(
    fun: Callable[[_T1, _T2, _T3, _T4], _U]
) -> Callable[[tuple[tuple[tuple[_T1, _T2], _T3], _T4]], _U]:
    def lifted(quadruple: tuple[tuple[tuple[_T1, _T2], _T3], _T4]) -> _U:
        ((a, b), c), d = quadruple
        return fun(a, b, c, d)

    return lifted


def lift6(
    fun: Callable[[_T1, _T2, _T3, _T4, _T5, _T6], _U]
) -> Callable[[tuple[tuple[tuple[tuple[tuple[_T1, _T2], _T3], _T4], _T5], _T6]], _U]:
    def lifted(
        sextuple: tuple[tuple[tuple[tuple[tuple[_T1, _T2], _T3], _T4], _T5], _T6]
    ) -> _U:
        (((((a, b), c), d), e), f) = sextuple
        return fun(a, b, c, d, e, f)

    return lifted


def lift7(
    fun: Callable[[_T1, _T2, _T3, _T4, _T5, _T6, _T7], _U]
) -> Callable[
    [tuple[tuple[tuple[tuple[tuple[tuple[_T1, _T2], _T3], _T4], _T5], _T6], _T7]], _U
]:
    def lifted(
        septuple: tuple[
            tuple[tuple[tuple[tuple[tuple[_T1, _T2], _T3], _T4], _T5], _T6], _T7
        ]
    ) -> _U:
        (((((a, b), c), d), e), f), g = septuple
        return fun(a, b, c, d, e, f, g)

    return lifted


def default(default_value: Callable[[], _T]) -> Callable[[_T | None], _T]:
    def defaulted(value: _T | None) -> _T:
        if value is None:
            return default_value()
        return value

    return defaulted


def string(expected: str) -> Parser[str, str]:
    length = len(expected)

    @SimpleParser
    def parser(text: str, index: int) -> Value[str]:
        if len(text) >= index + length and text[index : index + length] == expected:
            return Success(index + length, expected)
        else:
            return Failure(index, expected)

    return parser


def regex(expression: str) -> Parser[str, str]:
    compiled = re.compile(expression)

    @SimpleParser
    def parser(text: str, index: int) -> Value[str]:
        if match := compiled.match(text, index):
            entire_match = match[0]
            return Success(index + len(entire_match), entire_match)
        else:
            return Failure(index, expression)

    return parser


whitespace = regex(r"\s*")


def token(parser: Parser[str, _U]) -> Parser[str, _U]:
    return whitespace >> parser << whitespace
