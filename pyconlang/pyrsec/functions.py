from typing import Callable, TypeVar

_U = TypeVar("_U", covariant=True)

_T = TypeVar("_T")
_T1 = TypeVar("_T1", contravariant=True)
_T2 = TypeVar("_T2", contravariant=True)
_T3 = TypeVar("_T3", contravariant=True)
_T4 = TypeVar("_T4", contravariant=True)
_T5 = TypeVar("_T5", contravariant=True)
_T6 = TypeVar("_T6", contravariant=True)
_T7 = TypeVar("_T7", contravariant=True)


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


def lift5(
    fun: Callable[[_T1, _T2, _T3, _T4, _T5], _U]
) -> Callable[[tuple[tuple[tuple[tuple[_T1, _T2], _T3], _T4], _T5]], _U]:
    def lifted(quintuple: tuple[tuple[tuple[tuple[_T1, _T2], _T3], _T4], _T5]) -> _U:
        (((a, b), c), d), e = quintuple
        return fun(a, b, c, d, e)

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
